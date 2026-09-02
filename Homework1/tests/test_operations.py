from decimal import Decimal

import pytest

from account import Account
from operation import PreparedOperationState
from operations import (
    DepositOperation,
    WithdrawOperation,
)


@pytest.mark.parametrize(
    ("operation", "expected_name"),
    [
        (DepositOperation(), "deposit"),
        (WithdrawOperation(), "withdraw"),
    ],
)
def test_operation_exposes_configuration_name(
    operation: DepositOperation | WithdrawOperation,
    expected_name: str,
) -> None:
    assert operation.name == expected_name


def test_deposit_prepare_does_not_change_balance() -> None:
    account = Account("A", "100.00")
    operation = DepositOperation()

    prepared = operation.prepare(
        (Decimal("30.00"), account)
    )

    assert prepared.name == "deposit"
    assert (
        prepared.state
        is PreparedOperationState.PREPARED
    )
    assert account.balance == Decimal("100.00")
    assert account.reserved == Decimal("0")


def test_deposit_commit_increases_balance() -> None:
    account = Account("A", "100.00")
    prepared = DepositOperation().prepare(
        (Decimal("30.00"), account)
    )

    prepared.commit()

    assert account.balance == Decimal("130.00")
    assert account.reserved == Decimal("0")
    assert (
        prepared.state
        is PreparedOperationState.COMMITTED
    )


def test_deposit_rollback_leaves_balance_unchanged() -> None:
    account = Account("A", "100.00")
    prepared = DepositOperation().prepare(
        (Decimal("30.00"), account)
    )

    prepared.rollback()

    assert account.balance == Decimal("100.00")
    assert account.reserved == Decimal("0")
    assert (
        prepared.state
        is PreparedOperationState.ROLLED_BACK
    )


def test_withdraw_prepare_reserves_funds() -> None:
    account = Account("A", "100.00")
    operation = WithdrawOperation()

    prepared = operation.prepare(
        (Decimal("30.00"), account)
    )

    assert prepared is not None
    assert prepared.name == "withdraw"
    assert account.balance == Decimal("100.00")
    assert account.reserved == Decimal("30.00")
    assert account.available_balance == Decimal("70.00")


def test_withdraw_commit_reduces_balance() -> None:
    account = Account("A", "100.00")
    prepared = WithdrawOperation().prepare(
        (Decimal("30.00"), account)
    )

    assert prepared is not None

    prepared.commit()

    assert account.balance == Decimal("70.00")
    assert account.reserved == Decimal("0")
    assert account.available_balance == Decimal("70.00")
    assert (
        prepared.state
        is PreparedOperationState.COMMITTED
    )


def test_withdraw_rollback_releases_reservation() -> None:
    account = Account("A", "100.00")
    prepared = WithdrawOperation().prepare(
        (Decimal("30.00"), account)
    )

    assert prepared is not None

    prepared.rollback()

    assert account.balance == Decimal("100.00")
    assert account.reserved == Decimal("0")
    assert account.available_balance == Decimal("100.00")
    assert (
        prepared.state
        is PreparedOperationState.ROLLED_BACK
    )


def test_withdraw_prepare_returns_none_for_insufficient_funds() -> None:
    account = Account("A", "20.00")

    prepared = WithdrawOperation().prepare(
        (Decimal("30.00"), account)
    )

    assert prepared is None
    assert account.balance == Decimal("20.00")
    assert account.reserved == Decimal("0")
    assert account.available_balance == Decimal("20.00")


@pytest.mark.parametrize(
    "operation",
    [
        DepositOperation(),
        WithdrawOperation(),
    ],
)
@pytest.mark.parametrize(
    "arguments",
    [
        (),
        (Decimal("10.00"),),
        (
            Decimal("10.00"),
            Account("A", "100.00"),
            "unexpected",
        ),
    ],
)
def test_operation_rejects_wrong_argument_count(
    operation: DepositOperation | WithdrawOperation,
    arguments: tuple[object, ...],
) -> None:
    with pytest.raises(
        ValueError,
        match="expects exactly two arguments",
    ):
        operation.prepare(arguments)


@pytest.mark.parametrize(
    "operation",
    [
        DepositOperation(),
        WithdrawOperation(),
    ],
)
def test_operation_requires_account_as_second_argument(
    operation: DepositOperation | WithdrawOperation,
) -> None:
    with pytest.raises(
        TypeError,
        match="expects an Account",
    ):
        operation.prepare(
            (
                Decimal("10.00"),
                "not-an-account",
            )
        )


@pytest.mark.parametrize(
    "operation",
    [
        DepositOperation(),
        WithdrawOperation(),
    ],
)
@pytest.mark.parametrize(
    "invalid_amount",
    [
        Decimal("0"),
        Decimal("-1"),
    ],
)
def test_operation_rejects_non_positive_amount(
    operation: DepositOperation | WithdrawOperation,
    invalid_amount: Decimal,
) -> None:
    account = Account("A", "100.00")

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        operation.prepare(
            (invalid_amount, account)
        )

    assert account.balance == Decimal("100.00")
    assert account.reserved == Decimal("0")


@pytest.mark.parametrize(
    "operation",
    [
        DepositOperation(),
        WithdrawOperation(),
    ],
)
def test_operation_rejects_invalid_monetary_value(
    operation: DepositOperation | WithdrawOperation,
) -> None:
    account = Account("A", "100.00")

    with pytest.raises(
        ValueError,
        match="Invalid monetary value",
    ):
        operation.prepare(
            ("not-a-number", account)
        )

    assert account.balance == Decimal("100.00")
    assert account.reserved == Decimal("0")