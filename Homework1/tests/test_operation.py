import pytest

from operation import (
    PreparedOperation,
    PreparedOperationState,
)


def create_prepared_operation(
    event_log: list[str],
) -> PreparedOperation:
    return PreparedOperation(
        name="test",
        _commit_action=(
            lambda: event_log.append("commit")
        ),
        _rollback_action=(
            lambda: event_log.append("rollback")
        ),
    )


def test_prepared_operation_starts_in_prepared_state() -> None:
    operation = create_prepared_operation([])

    assert (
        operation.state
        is PreparedOperationState.PREPARED
    )


def test_prepared_operation_normalizes_name() -> None:
    operation = PreparedOperation(
        name="  deposit  ",
        _commit_action=lambda: None,
        _rollback_action=lambda: None,
    )

    assert operation.name == "deposit"


@pytest.mark.parametrize(
    "invalid_name",
    [
        "",
        "   ",
    ],
)
def test_prepared_operation_rejects_empty_name(
    invalid_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="name cannot be empty",
    ):
        PreparedOperation(
            name=invalid_name,
            _commit_action=lambda: None,
            _rollback_action=lambda: None,
        )


def test_commit_executes_action_and_changes_state() -> None:
    event_log: list[str] = []
    operation = create_prepared_operation(event_log)

    operation.commit()

    assert event_log == ["commit"]
    assert (
        operation.state
        is PreparedOperationState.COMMITTED
    )


def test_rollback_executes_action_and_changes_state() -> None:
    event_log: list[str] = []
    operation = create_prepared_operation(event_log)

    operation.rollback()

    assert event_log == ["rollback"]
    assert (
        operation.state
        is PreparedOperationState.ROLLED_BACK
    )


def test_operation_cannot_be_committed_twice() -> None:
    event_log: list[str] = []
    operation = create_prepared_operation(event_log)
    operation.commit()

    with pytest.raises(
        RuntimeError,
        match="current state is 'committed'",
    ):
        operation.commit()

    assert event_log == ["commit"]


def test_operation_cannot_be_rolled_back_twice() -> None:
    event_log: list[str] = []
    operation = create_prepared_operation(event_log)
    operation.rollback()

    with pytest.raises(
        RuntimeError,
        match="current state is 'rolled_back'",
    ):
        operation.rollback()

    assert event_log == ["rollback"]


def test_committed_operation_cannot_be_rolled_back() -> None:
    event_log: list[str] = []
    operation = create_prepared_operation(event_log)
    operation.commit()

    with pytest.raises(
        RuntimeError,
        match="Cannot rollback",
    ):
        operation.rollback()

    assert event_log == ["commit"]
    assert (
        operation.state
        is PreparedOperationState.COMMITTED
    )


def test_rolled_back_operation_cannot_be_committed() -> None:
    event_log: list[str] = []
    operation = create_prepared_operation(event_log)
    operation.rollback()

    with pytest.raises(
        RuntimeError,
        match="Cannot commit",
    ):
        operation.commit()

    assert event_log == ["rollback"]
    assert (
        operation.state
        is PreparedOperationState.ROLLED_BACK
    )


def test_failed_commit_action_preserves_prepared_state() -> None:
    def failing_commit() -> None:
        raise RuntimeError("Simulated commit failure.")

    operation = PreparedOperation(
        name="failing",
        _commit_action=failing_commit,
        _rollback_action=lambda: None,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated commit failure",
    ):
        operation.commit()

    assert (
        operation.state
        is PreparedOperationState.PREPARED
    )