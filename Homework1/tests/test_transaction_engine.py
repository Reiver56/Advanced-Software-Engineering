from decimal import Decimal
from pathlib import Path

import pytest

from account import Account
from operation import (
    Operation,
    OperationArguments,
    PreparedOperation,
)
from operations import (
    DepositOperation,
    WithdrawOperation,
)
from transaction_config import TransactionConfig
from transaction_engine import TransactionEngine


class RejectOperation(Operation):
    """Test operation that always rejects preparation."""

    @property
    def name(self) -> str:
        return "reject"

    def prepare(
        self,
        arguments: OperationArguments,
    ) -> PreparedOperation | None:
        return None


def create_configuration(
    tmp_path: Path,
    *,
    descriptions: str = (
        'transfer ["deposit", "withdraw"]\n'
    ),
    data: str = (
        "transfer [0, 1] [0, 2]\n"
    ),
) -> TransactionConfig:
    descriptions_path = (
        tmp_path / "descriptions.txt"
    )
    data_path = tmp_path / "data.txt"

    descriptions_path.write_text(
        descriptions,
        encoding="utf-8",
    )
    data_path.write_text(
        data,
        encoding="utf-8",
    )

    return TransactionConfig.from_files(
        descriptions_path,
        data_path,
    )


def create_engine(
    configuration: TransactionConfig,
) -> TransactionEngine:
    engine = TransactionEngine(configuration)
    engine.register(DepositOperation())
    engine.register(WithdrawOperation())

    return engine


def test_successful_transfer_commits_all_operations(
    tmp_path: Path,
) -> None:
    configuration = create_configuration(tmp_path)
    engine = create_engine(configuration)

    source = Account("SOURCE", "100.00")
    destination = Account("DESTINATION", "20.00")

    result = engine.execute(
        "transfer",
        (
            Decimal("30.00"),
            destination,
            source,
        ),
    )

    assert result is True
    assert source.balance == Decimal("70.00")
    assert destination.balance == Decimal("50.00")
    assert source.reserved == Decimal("0")
    assert destination.reserved == Decimal("0")


def test_failed_transfer_leaves_balances_unchanged(
    tmp_path: Path,
) -> None:
    configuration = create_configuration(tmp_path)
    engine = create_engine(configuration)

    source = Account("SOURCE", "20.00")
    destination = Account("DESTINATION", "50.00")

    result = engine.execute(
        "transfer",
        (
            Decimal("100.00"),
            destination,
            source,
        ),
    )

    assert result is False
    assert source.balance == Decimal("20.00")
    assert destination.balance == Decimal("50.00")
    assert source.reserved == Decimal("0")
    assert destination.reserved == Decimal("0")


def test_rejected_operation_rolls_back_previous_reservation(
    tmp_path: Path,
) -> None:
    configuration = create_configuration(
        tmp_path,
        descriptions=(
            'test_transaction ["withdraw", "reject"]\n'
        ),
        data=(
            "test_transaction [0, 1] [1]\n"
        ),
    )

    engine = create_engine(configuration)
    engine.register(RejectOperation())

    source = Account("SOURCE", "100.00")

    result = engine.execute(
        "test_transaction",
        (
            Decimal("30.00"),
            source,
        ),
    )

    assert result is False
    assert source.balance == Decimal("100.00")
    assert source.reserved == Decimal("0")
    assert source.available_balance == Decimal("100.00")


def test_unknown_transaction_is_rejected(
    tmp_path: Path,
) -> None:
    configuration = create_configuration(tmp_path)
    engine = create_engine(configuration)

    with pytest.raises(
        KeyError,
        match="Unknown transaction",
    ):
        engine.execute(
            "unknown",
            (),
        )


def test_unregistered_operation_is_rejected(
    tmp_path: Path,
) -> None:
    configuration = create_configuration(
        tmp_path,
        descriptions=(
            'custom ["missing_operation"]\n'
        ),
        data="custom [0]\n",
    )
    engine = TransactionEngine(configuration)

    with pytest.raises(
        KeyError,
        match="unregistered operations",
    ):
        engine.execute(
            "custom",
            ("value",),
        )


def test_invalid_argument_mapping_rolls_back_prepared_operations(
    tmp_path: Path,
) -> None:
    configuration = create_configuration(
        tmp_path,
        descriptions=(
            'broken ["withdraw", "deposit"]\n'
        ),
        data=(
            "broken [0, 1] [0, 2]\n"
        ),
    )
    engine = create_engine(configuration)

    source = Account("SOURCE", "100.00")

    with pytest.raises(
        ValueError,
        match="cannot apply argument mapping",
    ):
        engine.execute(
            "broken",
            (
                Decimal("30.00"),
                source,
            ),
        )

    assert source.balance == Decimal("100.00")
    assert source.reserved == Decimal("0")


def test_operation_cannot_be_registered_twice(
    tmp_path: Path,
) -> None:
    configuration = create_configuration(tmp_path)
    engine = TransactionEngine(configuration)

    engine.register(DepositOperation())

    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        engine.register(DepositOperation())