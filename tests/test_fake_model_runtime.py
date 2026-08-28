import asyncio

import pytest

from app.model_runtime import (
    FakeModelRuntime,
    ModelCompleted,
    ModelDelta,
    ModelRequest,
    ModelStarted,
    RuntimeFailureError,
)
from tests.runtime_contract import ModelRuntimeContract


class TestFakeModelRuntimeContract(ModelRuntimeContract):
    expected_text = "Contract fake response"

    def create_runtime(self) -> FakeModelRuntime:
        return FakeModelRuntime(chunks=("Contract ", "fake response"))


def make_request() -> ModelRequest:
    return ModelRequest(
        request_id="fake-request",
        system_text="Application policy",
        user_text="User prompt",
    )


def test_fake_runtime_streams_deterministic_text_chunks() -> None:
    async def collect_events():
        runtime = FakeModelRuntime(chunks=("Deterministic ", "response"))
        return [event async for event in runtime.stream_chat(make_request())]

    events = asyncio.run(collect_events())

    assert isinstance(events[0], ModelStarted)
    assert [event.text for event in events if isinstance(event, ModelDelta)] == [
        "Deterministic ",
        "response",
    ]
    assert isinstance(events[-1], ModelCompleted)


def test_fake_runtime_gate_releases_stream_without_timing_delay() -> None:
    async def exercise_gate():
        gate = asyncio.Event()
        runtime = FakeModelRuntime(chunks=("released",), chunk_gate=gate)
        stream = runtime.stream_chat(make_request())

        started = await anext(stream)
        next_event = asyncio.create_task(anext(stream))
        await asyncio.sleep(0)
        blocked_before_release = not next_event.done()
        gate.set()
        delta = await next_event
        completed = await anext(stream)
        return started, blocked_before_release, delta, completed

    started, blocked_before_release, delta, completed = asyncio.run(exercise_gate())

    assert isinstance(started, ModelStarted)
    assert blocked_before_release
    assert delta == ModelDelta(request_id="fake-request", text="released")
    assert isinstance(completed, ModelCompleted)


def test_fake_runtime_injects_known_runtime_failure() -> None:
    async def exercise_failure():
        failure = RuntimeFailureError("injected failure")
        runtime = FakeModelRuntime(failure=failure)
        stream = runtime.stream_chat(make_request())

        started = await anext(stream)
        with pytest.raises(RuntimeFailureError, match="injected failure") as raised:
            await anext(stream)
        return started, raised.value

    started, failure = asyncio.run(exercise_failure())

    assert isinstance(started, ModelStarted)
    assert failure.code.value == "runtime_failure"


def test_fake_runtime_tracks_abort_calls() -> None:
    runtime = FakeModelRuntime()

    asyncio.run(runtime.abort("request-to-stop"))

    assert runtime.abort_calls == ("request-to-stop",)
