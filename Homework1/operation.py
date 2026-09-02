"""Common abstractions for transactional primitive operations."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto


OperationArguments = tuple[object, ...]
TransactionAction = Callable[[], None]


class PreparedOperationState(Enum):
    """Lifecycle states of a successfully prepared operation."""

    PREPARED = auto()
    COMMITTED = auto()
    ROLLED_BACK = auto()


@dataclass(slots=True)
class PreparedOperation:
    """Operation that passed preparation and awaits a final decision."""

    name: str
    _commit_action: TransactionAction = field(
        repr=False,
    )
    _rollback_action: TransactionAction = field(
        repr=False,
    )
    _state: PreparedOperationState = field(
        default=PreparedOperationState.PREPARED,
        init=False,
    )

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValueError(
                "Prepared operation name cannot be empty."
            )

        self.name = normalized_name

    @property
    def state(self) -> PreparedOperationState:
        """Return the current operation lifecycle state."""
        return self._state

    def commit(self) -> None:
        """Execute the permanent action exactly once."""
        self._ensure_is_prepared("commit")

        self._commit_action()
        self._state = PreparedOperationState.COMMITTED

    def rollback(self) -> None:
        """Cancel the prepared action exactly once."""
        self._ensure_is_prepared("rollback")

        self._rollback_action()
        self._state = PreparedOperationState.ROLLED_BACK

    def _ensure_is_prepared(
        self,
        requested_action: str,
    ) -> None:
        if self._state is PreparedOperationState.PREPARED:
            return

        raise RuntimeError(
            f"Cannot {requested_action} operation "
            f"'{self.name}' because its current state is "
            f"'{self._state.name.lower()}'."
        )


class Operation(ABC):
    """Contract implemented by every primitive operation."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name used in transaction configurations."""

    @abstractmethod
    def prepare(
        self,
        arguments: OperationArguments,
    ) -> PreparedOperation | None:
        """
        Validate and prepare the operation.

        Return a PreparedOperation when preparation succeeds.
        Return None when a domain condition prevents execution.
        """