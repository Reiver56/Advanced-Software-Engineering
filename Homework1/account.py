"""Domain model for accounts managed by the transaction engine."""

from decimal import Decimal, InvalidOperation


MoneyValue = Decimal | int | float | str
ZERO = Decimal("0")


def to_decimal(value: MoneyValue) -> Decimal:
    """Convert a supported value into a finite Decimal."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(
            f"Invalid monetary value: {value!r}."
        ) from error

    if not amount.is_finite():
        raise ValueError(
            "A monetary value must be finite."
        )

    return amount


class Account:
    """Bank account supporting temporary withdrawal reservations."""

    __slots__ = (
        "_account_id",
        "_balance",
        "_reserved",
    )

    def __init__(
        self,
        account_id: str,
        initial_balance: MoneyValue = ZERO,
    ) -> None:
        normalized_id = account_id.strip()

        if not normalized_id:
            raise ValueError(
                "Account id cannot be empty."
            )

        balance = to_decimal(initial_balance)

        if balance < ZERO:
            raise ValueError(
                "Initial balance cannot be negative."
            )

        self._account_id = normalized_id
        self._balance = balance
        self._reserved = ZERO

    @property
    def account_id(self) -> str:
        """Return the immutable account identifier."""
        return self._account_id

    @property
    def balance(self) -> Decimal:
        """Return the permanently confirmed balance."""
        return self._balance

    @property
    def reserved(self) -> Decimal:
        """Return the amount reserved by prepared withdrawals."""
        return self._reserved

    @property
    def available_balance(self) -> Decimal:
        """Return the balance that can still be reserved."""
        return self._balance - self._reserved

    def reserve(self, value: MoneyValue) -> bool:
        """Temporarily reserve money without changing the balance."""
        amount = self._positive_amount(value)

        if amount > self.available_balance:
            return False

        self._reserved += amount
        return True

    def release(self, value: MoneyValue) -> None:
        """Release money reserved during the prepare phase."""
        amount = self._positive_amount(value)

        if amount > self._reserved:
            raise ValueError(
                "Cannot release more money than "
                "the reserved amount."
            )

        self._reserved -= amount

    def commit_withdrawal(
        self,
        value: MoneyValue,
    ) -> None:
        """Convert a reservation into a permanent withdrawal."""
        amount = self._positive_amount(value)

        if amount > self._reserved:
            raise ValueError(
                "A withdrawal must be reserved "
                "before it is committed."
            )

        self._reserved -= amount
        self._balance -= amount

    def deposit(self, value: MoneyValue) -> None:
        """Permanently add money to the account."""
        self._balance += self._positive_amount(value)

    @staticmethod
    def _positive_amount(
        value: MoneyValue,
    ) -> Decimal:
        amount = to_decimal(value)

        if amount <= ZERO:
            raise ValueError(
                "Transaction amount must be greater than zero."
            )

        return amount

    def __repr__(self) -> str:
        return (
            "Account("
            f"account_id={self.account_id!r}, "
            f"balance={self.balance}, "
            f"reserved={self.reserved}"
            ")"
        )