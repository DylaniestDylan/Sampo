import asyncio
from dataclasses import fields

import pytest

from app.workspace import (
    MAX_GENERATION_ERROR_CHARS,
    GenerationEvent,
    GenerationEventBuffer,
    GenerationEventName,
    GenerationRegistry,
    GenerationRegistryCapacityError,
    GenerationStatus,
    InvalidGenerationTransitionError,
)


def test_generation_state_contains_only_bounded_ephemeral_summary() -> None:
    registry = GenerationRegistry()

    state = registry.create()

    assert {field.name for field in fields(state)} == {
        "generation_id",
        "status",
        "error",
    }
    assert state.status is GenerationStatus.STREAMING
    assert state.error is None


def test_registry_owns_ephemeral_generation_state() -> None:
    registry = GenerationRegistry()
    state = registry.create()

    assert registry.get(state.generation_id) == state
    assert registry.get("unknown-generation") is None


def test_browser_generation_id_is_opaque_and_distinct_from_runtime_request_id() -> None:
    registry = GenerationRegistry()
    state = registry.create()
    runtime_request_id = registry.runtime_request_id(state.generation_id)

    assert len(state.generation_id) >= 32
    assert runtime_request_id is not None
    assert runtime_request_id != state.generation_id


@pytest.mark.parametrize(
    "terminal_status",
    [GenerationStatus.COMPLETED, GenerationStatus.STOPPED],
)
def test_generation_transitions_once_to_non_failure_terminal_state(
    terminal_status: GenerationStatus,
) -> None:
    registry = GenerationRegistry()
    state = registry.create()

    terminal = registry.transition(state.generation_id, terminal_status)

    assert terminal is not None
    assert terminal.status is terminal_status
    assert terminal.error is None
    with pytest.raises(InvalidGenerationTransitionError, match="already terminal"):
        registry.transition(state.generation_id, GenerationStatus.COMPLETED)


def test_failed_generation_stores_only_bounded_error_summary() -> None:
    registry = GenerationRegistry()
    state = registry.create()

    terminal = registry.transition(
        state.generation_id,
        GenerationStatus.FAILED,
        error="x" * (MAX_GENERATION_ERROR_CHARS + 100),
    )

    assert terminal is not None
    assert terminal.status is GenerationStatus.FAILED
    assert terminal.error == "x" * MAX_GENERATION_ERROR_CHARS


def test_registry_capacity_evicts_terminal_state_but_not_active_state() -> None:
    registry = GenerationRegistry(capacity=1)
    active = registry.create()

    with pytest.raises(GenerationRegistryCapacityError, match="too many active"):
        registry.create()

    registry.transition(active.generation_id, GenerationStatus.COMPLETED)
    replacement = registry.create()
    assert registry.get(active.generation_id) is None
    assert registry.get(replacement.generation_id) == replacement


def test_event_buffer_is_bounded_and_reports_slow_consumer() -> None:
    buffer = GenerationEventBuffer(capacity=1)
    started = GenerationEvent(name=GenerationEventName.STARTED)
    delta = GenerationEvent(name=GenerationEventName.DELTA, text="chunk")

    assert buffer.publish(started)
    assert not buffer.publish(delta)
    assert buffer.size == buffer.capacity == 1
    assert asyncio.run(buffer.receive()) == started


def test_event_buffer_can_replace_backlog_with_truthful_terminal_event() -> None:
    buffer = GenerationEventBuffer(capacity=2)
    buffer.publish(GenerationEvent(name=GenerationEventName.STARTED))
    buffer.publish(GenerationEvent(name=GenerationEventName.DELTA, text="partial"))
    failed = GenerationEvent(
        name=GenerationEventName.FAILED,
        error="event consumer could not keep up",
    )

    buffer.replace_with(failed)

    assert buffer.size == 1
    assert asyncio.run(buffer.receive()) == failed
