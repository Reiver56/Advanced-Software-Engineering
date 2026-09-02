"""Primitive banking operations used by the transaction engine."""

from decimal import Decimal

from account import Account, MoneyValue, ZERO, to_decimal
from operation import (
    Operation,
    OperationArguments,
    PreparedOperation,
)


def _extract_amount_and_account(
    operation_name: str,
    arguments: OperationArguments,
) -> tuple[Decimal, Account]:
    """Validate and extract the common banking arguments."""
    if len(arguments) != 2:
        raise ValueError(
            f"Operation '{operation_name}' expects exactly "
            "two arguments: amount and account."
        )

    raw_amount, raw_account = arguments
    amount = to_decimal(raw_amount)

    if amount <= ZERO:
        raise ValueError(
            f"Operation '{operation_name}' requires "
            "an amount greater than zero."
        )

    if not isinstance(raw_account, Account):
        raise TypeError(
            f"Operation '{operation_name}' expects "
            "an Account as its second argument."
        )

    return amount, raw_account


class DepositOperation(Operation):
    """Prepare and commit a deposit into an account."""

    @property
    def name(self) -> str:
        """Return the configuration name of this operation."""
        return "deposit"

    def prepare(
        self,
        arguments: OperationArguments,
    ) -> PreparedOperation:
        """
        Validate a deposit and return its prepared representation.

        A deposit does not need to reserve existing resources.
        The balance is changed only if commit is later requested.
        """
        amount, account = _extract_amount_and_account(
            self.name,
            arguments,
        )

        return PreparedOperation(
            name=self.name,
            _commit_action=lambda: account.deposit(amount),
            _rollback_action=lambda: None,
        )


class WithdrawOperation(Operation):
    """Reserve funds and prepare a withdrawal from an account."""

    @property
    def name(self) -> str:
        """Return the configuration name of this operation."""
        return "withdraw"

    def prepare(
        self,
        arguments: OperationArguments,
    ) -> PreparedOperation | None:
        """
        Reserve the requested amount before creating the operation.

        Return None when the account has insufficient available funds.
        """
        amount, account = _extract_amount_and_account(
            self.name,
            arguments,
        )

        if not account.reserve(amount):
            return None

        return PreparedOperation(
            name=self.name,
            _commit_action=(
                lambda: account.commit_withdrawal(amount)
            ),
            _rollback_action=(
                lambda: account.release(amount)
            ),
        )