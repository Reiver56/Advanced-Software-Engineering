from decimal import Decimal

import pytest

from account import Account


def test_account_normalizes_identifier_and_balance() -> None:
    account = Account(
        account_id="  SAVINGS  ",
        initial_balance="100.50",
    )

    assert account.account_id == "SAVINGS"
    assert account.balance == Decimal("100.50")
    assert account.reserved == Decimal("0")
    assert account.available_balance == Decimal("100.50")


@pytest.mark.parametrize(
    "account_id",
    [
        "",
        "   ",
    ],
)
def test_account_rejects_empty_identifier(
    account_id: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="Account id cannot be empty",
    ):
        Account(account_id)


def test_account_rejects_negative_initial_balance() -> None:
    with pytest.raises(
        ValueError,
        match="Initial balance cannot be negative",
    ):
        Account(
            account_id="A",
            initial_balance="-0.01",
        )


@pytest.mark.parametrize(
    "invalid_value",
    [
        "not-a-number",
        "NaN",
        "Infinity",
    ],
)
def test_account_rejects_invalid_monetary_values(
    invalid_value: str,
) -> None:
    with pytest.raises(ValueError):
        Account(
            account_id="A",
            initial_balance=invalid_value,
        )


def test_reserve_blocks_money_without_changing_balance() -> None:
    account = Account("A", "100.00")

    result = account.reserve("30.00")

    assert result is True
    assert account.balance == Decimal("100.00")
    assert account.reserved == Decimal("30.00")
    assert account.available_balance == Decimal("70.00")


def test_reserve_returns_false_for_insufficient_funds() -> None:
    account = Account("A", "20.00")

    result = account.reserve("30.00")

    assert result is False
    assert account.balance == Decimal("20.00")
    assert account.reserved == Decimal("0")
    assert account.available_balance == Decimal("20.00")


def test_reservations_use_only_available_balance() -> None:
    account = Account("A", "100.00")

    first_result = account.reserve("60.00")
    second_result = account.reserve("50.00")

    assert first_result is True
    assert second_result is False
    assert account.balance == Decimal("100.00")
    assert account.reserved == Decimal("60.00")
    assert account.available_balance == Decimal("40.00")


def test_release_cancels_existing_reservation() -> None:
    account = Account("A", "100.00")
    account.reserve("30.00")

    account.release("30.00")

    assert account.balance == Decimal("100.00")
    assert account.reserved == Decimal("0")
    assert account.available_balance == Decimal("100.00")


def test_release_rejects_amount_greater_than_reservation() -> None:
    account = Account("A", "100.00")
    account.reserve("20.00")

    with pytest.raises(
        ValueError,
        match="Cannot release more money",
    ):
        account.release("30.00")

    assert account.balance == Decimal("100.00")
    assert account.reserved == Decimal("20.00")


def test_commit_withdrawal_updates_confirmed_balance() -> None:
    account = Account("A", "100.00")
    account.reserve("30.00")

    account.commit_withdrawal("30.00")

    assert account.balance == Decimal("70.00")
    assert account.reserved == Decimal("0")
    assert account.available_balance == Decimal("70.00")


def test_withdrawal_cannot_commit_without_reservation() -> None:
    account = Account("A", "100.00")

    with pytest.raises(
        ValueError,
        match="must be reserved",
    ):
        account.commit_withdrawal("30.00")

    assert account.balance == Decimal("100.00")
    assert account.reserved == Decimal("0")


def test_deposit_increases_confirmed_balance() -> None:
    account = Account("A", "100.00")

    account.deposit("25.50")

    assert account.balance == Decimal("125.50")
    assert account.reserved == Decimal("0")
    assert account.available_balance == Decimal("125.50")


@pytest.mark.parametrize(
    "method_name",
    [
        "reserve",
        "deposit",
    ],
)
@pytest.mark.parametrize(
    "invalid_amount",
    [
        "0",
        "-1",
    ],
)
def test_account_rejects_non_positive_transaction_amounts(
    method_name: str,
    invalid_amount: str,
) -> None:
    account = Account("A", "100.00")
    method = getattr(account, method_name)

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        method(invalid_amount)

    assert account.balance == Decimal("100.00")
    assert account.reserved == Decimal("0")