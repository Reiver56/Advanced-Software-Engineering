"""Generic coordinator for configured composite transactions."""

from collections.abc import Sequence

from operation import (
    Operation,
    OperationArguments,
    PreparedOperation,
)
from transaction_config import (
    TransactionConfig,
    TransactionDefinition,
)


class TransactionEngine:
    """Execute configured transactions using prepare, commit and rollback."""

    def __init__(
        self,
        configuration: TransactionConfig,
    ) -> None:
        self._configuration = configuration
        self._operations: dict[str, Operation] = {}

    def register(
        self,
        operation: Operation,
    ) -> None:
        """Register one primitive operation by its public name."""
        operation_name = operation.name.strip()

        if not operation_name:
            raise ValueError(
                "Operation name cannot be empty."
            )

        if operation_name in self._operations:
            raise ValueError(
                f"Operation '{operation_name}' "
                "is already registered."
            )

        self._operations[operation_name] = operation

    def execute(
        self,
        transaction_name: str,
        arguments: Sequence[object],
    ) -> bool:
        """
        Execute a configured composite transaction.

        Return True after a complete commit.
        Return False when an operation cannot be prepared.
        """
        definition = self._configuration.definition_for(
            transaction_name
        )

        self._validate_registered_operations(definition)

        prepared_operations: list[
            PreparedOperation
        ] = []

        try:
            for operation_name, mapping in zip(
                definition.operation_names,
                definition.argument_mappings,
                strict=True,
            ):
                operation = self._operations[
                    operation_name
                ]

                operation_arguments = (
                    self._extract_arguments(
                        transaction_name,
                        arguments,
                        mapping,
                    )
                )

                prepared_operation = operation.prepare(
                    operation_arguments
                )

                if prepared_operation is None:
                    self._rollback(
                        prepared_operations
                    )
                    return False

                prepared_operations.append(
                    prepared_operation
                )

        except Exception:
            self._rollback(prepared_operations)
            raise

        self._commit(prepared_operations)
        return True

    def _validate_registered_operations(
        self,
        definition: TransactionDefinition,
    ) -> None:
        missing_operations = {
            operation_name
            for operation_name
            in definition.operation_names
            if operation_name
            not in self._operations
        }

        if not missing_operations:
            return

        missing_names = ", ".join(
            sorted(missing_operations)
        )

        raise KeyError(
            f"Transaction '{definition.name}' uses "
            f"unregistered operations: {missing_names}."
        )

    @staticmethod
    def _extract_arguments(
        transaction_name: str,
        arguments: Sequence[object],
        mapping: tuple[int, ...],
    ) -> OperationArguments:
        try:
            return tuple(
                arguments[index]
                for index in mapping
            )
        except IndexError as error:
            raise ValueError(
                f"Transaction '{transaction_name}' "
                f"cannot apply argument mapping "
                f"{mapping} to {len(arguments)} arguments."
            ) from error

    @staticmethod
    def _commit(
        prepared_operations: list[
            PreparedOperation
        ],
    ) -> None:
        for prepared_operation in prepared_operations:
            prepared_operation.commit()

    @staticmethod
    def _rollback(
        prepared_operations: list[
            PreparedOperation
        ],
    ) -> None:
        for prepared_operation in reversed(
            prepared_operations
        ):
            prepared_operation.rollback()