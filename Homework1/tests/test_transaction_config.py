from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from transaction_config import TransactionConfig


def write_configuration_files(
    tmp_path: Path,
    *,
    descriptions: str = (
        'transfer ["deposit", "withdraw"]\n'
    ),
    data: str = (
        "transfer [0, 1] [0, 2]\n"
    ),
) -> tuple[Path, Path]:
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

    return descriptions_path, data_path


def load_configuration(
    tmp_path: Path,
    *,
    descriptions: str = (
        'transfer ["deposit", "withdraw"]\n'
    ),
    data: str = (
        "transfer [0, 1] [0, 2]\n"
    ),
) -> TransactionConfig:
    descriptions_path, data_path = (
        write_configuration_files(
            tmp_path,
            descriptions=descriptions,
            data=data,
        )
    )

    return TransactionConfig.from_files(
        descriptions_path,
        data_path,
    )


def test_loads_valid_transaction_definition(
    tmp_path: Path,
) -> None:
    configuration = load_configuration(tmp_path)

    definition = configuration.definition_for(
        "transfer"
    )

    assert definition.name == "transfer"
    assert definition.operation_names == (
        "deposit",
        "withdraw",
    )
    assert definition.argument_mappings == (
        (0, 1),
        (0, 2),
    )


def test_ignores_comments_and_empty_lines(
    tmp_path: Path,
) -> None:
    configuration = load_configuration(
        tmp_path,
        descriptions=(
            "# Transaction descriptions\n"
            "\n"
            'transfer ["deposit", "withdraw"]\n'
        ),
        data=(
            "# Argument mappings\n"
            "\n"
            "transfer [0, 1] [0, 2]\n"
        ),
    )

    assert (
        configuration
        .definition_for("transfer")
        .operation_names
        == ("deposit", "withdraw")
    )


def test_loads_multiple_transactions(
    tmp_path: Path,
) -> None:
    configuration = load_configuration(
        tmp_path,
        descriptions=(
            'transfer ["deposit", "withdraw"]\n'
            'top_up ["deposit"]\n'
        ),
        data=(
            "transfer [0, 1] [0, 2]\n"
            "top_up [0, 1]\n"
        ),
    )

    transfer = configuration.definition_for(
        "transfer"
    )
    top_up = configuration.definition_for(
        "top_up"
    )

    assert transfer.operation_names == (
        "deposit",
        "withdraw",
    )
    assert top_up.operation_names == ("deposit",)
    assert top_up.argument_mappings == ((0, 1),)


def test_accepts_nested_mapping_list(
    tmp_path: Path,
) -> None:
    configuration = load_configuration(
        tmp_path,
        data=(
            "transfer [[0, 1], [0, 2]]\n"
        ),
    )

    definition = configuration.definition_for(
        "transfer"
    )

    assert definition.argument_mappings == (
        (0, 1),
        (0, 2),
    )


def test_rejects_unknown_transaction_name(
    tmp_path: Path,
) -> None:
    configuration = load_configuration(tmp_path)

    with pytest.raises(
        KeyError,
        match="Unknown transaction",
    ):
        configuration.definition_for("unknown")


def test_rejects_missing_configuration_file(
    tmp_path: Path,
) -> None:
    descriptions_path = (
        tmp_path / "missing_descriptions.txt"
    )
    data_path = tmp_path / "data.txt"
    data_path.write_text(
        "transfer [0, 1] [0, 2]\n",
        encoding="utf-8",
    )

    with pytest.raises(
        FileNotFoundError,
        match="Configuration file not found",
    ):
        TransactionConfig.from_files(
            descriptions_path,
            data_path,
        )


def test_rejects_empty_configuration_file(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="Configuration file is empty",
    ):
        load_configuration(
            tmp_path,
            descriptions="",
        )


def test_rejects_line_without_configuration_data(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="expected a transaction name",
    ):
        load_configuration(
            tmp_path,
            descriptions="transfer\n",
        )


def test_rejects_invalid_json_syntax(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="invalid configuration syntax",
    ):
        load_configuration(
            tmp_path,
            data="transfer [0, 1\n",
        )


def test_rejects_duplicate_transaction_name(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="duplicate transaction",
    ):
        load_configuration(
            tmp_path,
            descriptions=(
                'transfer ["deposit"]\n'
                'transfer ["withdraw"]\n'
            ),
        )


def test_rejects_non_matching_configuration_files(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="Configuration files do not match",
    ):
        load_configuration(
            tmp_path,
            descriptions=(
                'transfer ["deposit", "withdraw"]\n'
            ),
            data="top_up [0, 1]\n",
        )


def test_rejects_description_that_is_not_a_list(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="operations in one JSON list",
    ):
        load_configuration(
            tmp_path,
            descriptions='transfer "deposit"\n',
        )


def test_rejects_empty_operation_list(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="at least one operation",
    ):
        load_configuration(
            tmp_path,
            descriptions="transfer []\n",
            data="transfer [0, 1]\n",
        )


@pytest.mark.parametrize(
    "invalid_description",
    [
        'transfer ["deposit", ""]\n',
        'transfer ["deposit", 10]\n',
    ],
)
def test_rejects_invalid_operation_name(
    tmp_path: Path,
    invalid_description: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="invalid operation name",
    ):
        load_configuration(
            tmp_path,
            descriptions=invalid_description,
        )


def test_rejects_different_operation_and_mapping_counts(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "defines 2 operations but "
            "1 argument mappings"
        ),
    ):
        load_configuration(
            tmp_path,
            descriptions=(
                'transfer ["deposit", "withdraw"]\n'
            ),
            data="transfer [0, 1]\n",
        )


def test_rejects_empty_argument_mapping(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="invalid or empty argument mapping",
    ):
        load_configuration(
            tmp_path,
            descriptions='transfer ["deposit"]\n',
            data="transfer []\n",
        )


@pytest.mark.parametrize(
    "invalid_index",
    [
        "-1",
        "true",
        '"1"',
    ],
)
def test_rejects_invalid_argument_index(
    tmp_path: Path,
    invalid_index: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="invalid argument index",
    ):
        load_configuration(
            tmp_path,
            descriptions='transfer ["deposit"]\n',
            data=(
                f"transfer [0, {invalid_index}]\n"
            ),
        )


def test_transaction_definition_is_immutable(
    tmp_path: Path,
) -> None:
    configuration = load_configuration(tmp_path)
    definition = configuration.definition_for(
        "transfer"
    )

    with pytest.raises(FrozenInstanceError):
        definition.name = "changed"  # type: ignore[misc]