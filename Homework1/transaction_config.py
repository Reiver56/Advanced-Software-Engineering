"""Loading and validation of external transaction definitions."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TransactionDefinition:
    """Validated definition of a composite transaction."""

    name: str
    operation_names: tuple[str, ...]
    argument_mappings: tuple[tuple[int, ...], ...]


class TransactionConfig:
    """Collection of transaction definitions loaded from files."""

    def __init__(
        self,
        definitions: tuple[TransactionDefinition, ...],
    ) -> None:
        if not definitions:
            raise ValueError(
                "At least one transaction must be defined."
            )

        self._definitions = {
            definition.name: definition
            for definition in definitions
        }

        if len(self._definitions) != len(definitions):
            raise ValueError(
                "Transaction names must be unique."
            )

    @classmethod
    def from_files(
        cls,
        descriptions_path: str | Path,
        data_path: str | Path,
    ) -> "TransactionConfig":
        """Load and validate transaction definitions."""
        descriptions = _read_configuration_file(
            Path(descriptions_path)
        )
        mappings = _read_configuration_file(
            Path(data_path)
        )

        _validate_matching_transaction_names(
            descriptions,
            mappings,
        )

        definitions = tuple(
            _create_definition(
                transaction_name,
                descriptions[transaction_name],
                mappings[transaction_name],
            )
            for transaction_name in descriptions
        )

        return cls(definitions)

    def definition_for(
        self,
        transaction_name: str,
    ) -> TransactionDefinition:
        """Return the requested transaction definition."""
        try:
            return self._definitions[transaction_name]
        except KeyError as error:
            raise KeyError(
                f"Unknown transaction: "
                f"'{transaction_name}'."
            ) from error


def _read_configuration_file(
    path: Path,
) -> dict[str, tuple[object, ...]]:
    """Read transaction entries from one configuration file."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {path}."
        )

    entries: dict[str, tuple[object, ...]] = {}

    with path.open(
        mode="r",
        encoding="utf-8",
    ) as configuration_file:
        for line_number, raw_line in enumerate(
            configuration_file,
            start=1,
        ):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split(maxsplit=1)

            if len(parts) != 2:
                raise ValueError(
                    f"{path}:{line_number}: expected "
                    "a transaction name followed by data."
                )

            transaction_name, payload = parts

            if transaction_name in entries:
                raise ValueError(
                    f"{path}:{line_number}: duplicate "
                    f"transaction '{transaction_name}'."
                )

            entries[transaction_name] = (
                _decode_json_values(
                    payload,
                    path,
                    line_number,
                )
            )

    if not entries:
        raise ValueError(
            f"Configuration file is empty: {path}."
        )

    return entries


def _decode_json_values(
    payload: str,
    path: Path,
    line_number: int,
) -> tuple[object, ...]:
    """
    Decode one or more consecutive JSON values.

    This supports lines such as:

        transfer ["deposit", "withdraw"]
        transfer [0, 1] [0, 2]
    """
    decoder = json.JSONDecoder()
    values: list[object] = []
    position = 0

    while position < len(payload):
        while (
            position < len(payload)
            and payload[position].isspace()
        ):
            position += 1

        if position >= len(payload):
            break

        try:
            value, position = decoder.raw_decode(
                payload,
                position,
            )
        except json.JSONDecodeError as error:
            raise ValueError(
                f"{path}:{line_number}: invalid "
                f"configuration syntax: {error.msg}."
            ) from error

        values.append(value)

    if not values:
        raise ValueError(
            f"{path}:{line_number}: missing "
            "configuration data."
        )

    return tuple(values)


def _validate_matching_transaction_names(
    descriptions: dict[str, tuple[object, ...]],
    mappings: dict[str, tuple[object, ...]],
) -> None:
    description_names = set(descriptions)
    mapping_names = set(mappings)

    if description_names == mapping_names:
        return

    missing_mappings = (
        description_names - mapping_names
    )
    missing_descriptions = (
        mapping_names - description_names
    )

    details: list[str] = []

    if missing_mappings:
        details.append(
            "missing argument mappings for: "
            + ", ".join(sorted(missing_mappings))
        )

    if missing_descriptions:
        details.append(
            "missing operation descriptions for: "
            + ", ".join(sorted(missing_descriptions))
        )

    raise ValueError(
        "Configuration files do not match: "
        + "; ".join(details)
        + "."
    )


def _create_definition(
    transaction_name: str,
    raw_description: tuple[object, ...],
    raw_mappings: tuple[object, ...],
) -> TransactionDefinition:
    operation_names = _validate_operations(
        transaction_name,
        raw_description,
    )
    argument_mappings = _validate_mappings(
        transaction_name,
        raw_mappings,
    )

    if len(operation_names) != len(argument_mappings):
        raise ValueError(
            f"Transaction '{transaction_name}' defines "
            f"{len(operation_names)} operations but "
            f"{len(argument_mappings)} argument mappings."
        )

    return TransactionDefinition(
        name=transaction_name,
        operation_names=operation_names,
        argument_mappings=argument_mappings,
    )


def _validate_operations(
    transaction_name: str,
    raw_description: tuple[object, ...],
) -> tuple[str, ...]:
    if (
        len(raw_description) != 1
        or not isinstance(raw_description[0], list)
    ):
        raise ValueError(
            f"Transaction '{transaction_name}' must define "
            "its operations in one JSON list."
        )

    raw_operations = raw_description[0]

    if not raw_operations:
        raise ValueError(
            f"Transaction '{transaction_name}' "
            "must contain at least one operation."
        )

    if not all(
        isinstance(operation, str)
        and operation.strip()
        for operation in raw_operations
    ):
        raise ValueError(
            f"Transaction '{transaction_name}' contains "
            "an invalid operation name."
        )

    return tuple(
        operation.strip()
        for operation in raw_operations
    )


def _validate_mappings(
    transaction_name: str,
    raw_mappings: tuple[object, ...],
) -> tuple[tuple[int, ...], ...]:
    if (
        len(raw_mappings) == 1
        and isinstance(raw_mappings[0], list)
        and raw_mappings[0]
        and all(
            isinstance(mapping, list)
            for mapping in raw_mappings[0]
        )
    ):
        mappings = raw_mappings[0]
    else:
        mappings = raw_mappings

    validated_mappings: list[tuple[int, ...]] = []

    for mapping in mappings:
        if not isinstance(mapping, list) or not mapping:
            raise ValueError(
                f"Transaction '{transaction_name}' contains "
                "an invalid or empty argument mapping."
            )

        if not all(
            isinstance(index, int)
            and not isinstance(index, bool)
            and index >= 0
            for index in mapping
        ):
            raise ValueError(
                f"Transaction '{transaction_name}' contains "
                "an invalid argument index."
            )

        validated_mappings.append(tuple(mapping))

    if not validated_mappings:
        raise ValueError(
            f"Transaction '{transaction_name}' must define "
            "at least one argument mapping."
        )

    return tuple(validated_mappings)