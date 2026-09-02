"""Executable demonstration of the generic transaction engine."""

from decimal import Decimal
from pathlib import Path

from account import Account
from operations import (
    DepositOperation,
    WithdrawOperation,
)
from transaction_config import TransactionConfig
from transaction_engine import TransactionEngine


PROJECT_DIRECTORY = Path(__file__).resolve().parent


def create_engine() -> TransactionEngine:
    """Create and configure the transaction engine."""
    configuration = TransactionConfig.from_files(
        PROJECT_DIRECTORY / "descriptions.txt",
        PROJECT_DIRECTORY / "data.txt",
    )

    engine = TransactionEngine(configuration)

    engine.register(DepositOperation())
    engine.register(WithdrawOperation())

    return engine


def print_account(account: Account) -> None:
    """Print the relevant state of one account."""
    print(
        f"  {account.account_id}: "
        f"balance={account.balance:.2f}, "
        f"reserved={account.reserved:.2f}, "
        f"available={account.available_balance:.2f}"
    )


def print_accounts(
    source: Account,
    destination: Account,
) -> None:
    """Print the source and destination accounts."""
    print_account(source)
    print_account(destination)


def execute_transfer(
    engine: TransactionEngine,
    *,
    amount: Decimal,
    source: Account,
    destination: Account,
) -> bool:
    """Execute one configured transfer transaction."""
    return engine.execute(
        "transfer",
        (
            amount,
            destination,
            source,
        ),
    )


def main() -> None:
    """Run successful and failing transaction examples."""
    engine = create_engine()

    source = Account(
        account_id="SOURCE",
        initial_balance="100.00",
    )
    destination = Account(
        account_id="DESTINATION",
        initial_balance="20.00",
    )

    print("=== INITIAL STATE ===")
    print_accounts(source, destination)

    print()
    print("=== SUCCESSFUL TRANSFER ===")
    print("Transferring 30.00 from SOURCE to DESTINATION.")

    successful_result = execute_transfer(
        engine,
        amount=Decimal("30.00"),
        source=source,
        destination=destination,
    )

    print(
        "Result:",
        "COMMITTED"
        if successful_result
        else "ROLLED BACK",
    )
    print_accounts(source, destination)

    print()
    print("=== FAILED TRANSFER ===")
    print("Transferring 100.00 from SOURCE to DESTINATION.")

    source_balance_before = source.balance
    destination_balance_before = destination.balance

    failed_result = execute_transfer(
        engine,
        amount=Decimal("100.00"),
        source=source,
        destination=destination,
    )

    print(
        "Result:",
        "COMMITTED"
        if failed_result
        else "ROLLED BACK",
    )
    print_accounts(source, destination)

    balances_unchanged = (
        source.balance == source_balance_before
        and destination.balance
        == destination_balance_before
    )

    print()
    print(
        "Atomicity check:",
        "PASSED"
        if balances_unchanged
        else "FAILED",
    )


if __name__ == "__main__":
    main()