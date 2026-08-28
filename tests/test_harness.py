import asyncio
from dataclasses import fields
from inspect import signature

import pytest

import app.harness.core as harness_core
from app.harness import (
    MAX_HARNESS_CONTEXT_CHARS,
    PHASE_ONE_APPLICATION_POLICY,
    ApplicationHarness,
    HarnessPolicy,
    HarnessRequest,
    HarnessToolBoundary,
    ToolRegistry,
    assemble_model_request,
)
from app.model_runtime import (
    FakeModelRuntime,
    ModelCompleted,
    ModelDelta,
    ModelFailed,
    ModelRequest,
    ModelRuntime,
    ModelStarted,
    ModelStopped,
    RuntimeCancelledError,
    RuntimeFailureError,
)


def test_harness_request_contains_only_phase_one_inputs() -> None:
    request = HarnessRequest(request_id="request-1", user_prompt="User prompt")

    assert {field.name for field in fields(request)} == {
        "request_id",
        "user_prompt",
    }


@pytest.mark.parametrize("field_name", ["request_id", "user_prompt"])
def test_harness_request_rejects_blank_inputs(field_name: str) -> None:
    values = {"request_id": "request-1", "user_prompt": "User prompt"}
    values[field_name] = "  "

    with pytest.raises(ValueError, match=field_name):
        HarnessRequest(**values)


def test_harness_policy_is_explicit_backend_owned_input() -> None:
    policy = HarnessPolicy(application_text=PHASE_ONE_APPLICATION_POLICY)

    assert {field.name for field in fields(policy)} == {"application_text"}
    assert policy.application_text == "Answer the user's current request."


def test_harness_policy_rejects_blank_text() -> None:
    with pytest.raises(ValueError, match="application_text"):
        HarnessPolicy(application_text="  ")


def test_context_assembly_separates_policy_from_user_prompt() -> None:
    request = HarnessRequest(request_id="request-1", user_prompt="User prompt")
    policy = HarnessPolicy(application_text="Trusted application policy")

    model_request = assemble_model_request(request=request, policy=policy)

    assert model_request == ModelRequest(
        request_id="request-1",
        system_text="Trusted application policy",
        user_text="User prompt",
    )


def test_context_assembly_enforces_total_text_bound() -> None:
    policy = HarnessPolicy(application_text="Policy")
    prompt_at_limit = "x" * (
        MAX_HARNESS_CONTEXT_CHARS - len(policy.application_text)
    )

    assembled = assemble_model_request(
        request=HarnessRequest(
            request_id="bounded-request",
            user_prompt=prompt_at_limit,
        ),
        policy=policy,
    )

    assert assembled.user_text == prompt_at_limit
    with pytest.raises(ValueError, match="must not exceed"):
        assemble_model_request(
            request=HarnessRequest(
                request_id="oversized-request",
                user_prompt=f"{prompt_at_limit}x",
            ),
            policy=policy,
        )


def test_harness_invokes_only_the_injected_runtime() -> None:
    async def run_harness():
        runtime = FakeModelRuntime(chunks=("response",))
        harness = ApplicationHarness(
            runtime=runtime,
            policy=HarnessPolicy(application_text="Backend policy"),
            tool_boundary=HarnessToolBoundary(registry=ToolRegistry()),
        )
        events = [
            event
            async for event in harness.stream(
                HarnessRequest(request_id="request-1", user_prompt="User prompt")
            )
        ]
        return runtime, events

    runtime, events = asyncio.run(run_harness())

    assert len(events) == 3
    assert runtime.stream_requests == (
        ModelRequest(
            request_id="request-1",
            system_text="Backend policy",
            user_text="User prompt",
        ),
    )


def test_harness_forwards_normalized_stream_events() -> None:
    async def collect_events():
        harness = ApplicationHarness(
            runtime=FakeModelRuntime(chunks=("Streamed ", "response")),
            policy=HarnessPolicy(application_text="Backend policy"),
            tool_boundary=HarnessToolBoundary(registry=ToolRegistry()),
        )
        return [
            event
            async for event in harness.stream(
                HarnessRequest(
                    request_id="stream-request",
                    user_prompt="User prompt",
                )
            )
        ]

    events = asyncio.run(collect_events())

    assert events == [
        ModelStarted(request_id="stream-request"),
        ModelDelta(request_id="stream-request", text="Streamed "),
        ModelDelta(request_id="stream-request", text="response"),
        ModelCompleted(request_id="stream-request"),
    ]


@pytest.mark.parametrize(
    ("failure", "terminal_event"),
    [
        (
            RuntimeFailureError("local runtime failed"),
            ModelFailed(
                request_id="failed-request",
                message="local runtime failed",
            ),
        ),
        (
            RuntimeCancelledError("local runtime was cancelled"),
            ModelStopped(request_id="failed-request"),
        ),
    ],
)
def test_harness_translates_runtime_errors_to_truthful_terminal_events(
    failure,
    terminal_event,
) -> None:
    async def collect_events():
        harness = ApplicationHarness(
            runtime=FakeModelRuntime(
                chunks=("partial", "unreached"),
                failure=failure,
                failure_after_chunks=1,
            ),
            policy=HarnessPolicy(application_text="Backend policy"),
            tool_boundary=HarnessToolBoundary(registry=ToolRegistry()),
        )
        return [
            event
            async for event in harness.stream(
                HarnessRequest(
                    request_id="failed-request",
                    user_prompt="User prompt",
                )
            )
        ]

    events = asyncio.run(collect_events())

    assert events == [
        ModelStarted(request_id="failed-request"),
        ModelDelta(request_id="failed-request", text="partial"),
        terminal_event,
    ]
    assert not any(isinstance(event, ModelCompleted) for event in events)


def test_harness_cancellation_aborts_runtime_and_discards_late_chunks() -> None:
    async def collect_events():
        gate = asyncio.Event()
        cancellation_signal = asyncio.Event()
        runtime = FakeModelRuntime(chunks=("must not escape",), chunk_gate=gate)
        harness = ApplicationHarness(
            runtime=runtime,
            policy=HarnessPolicy(application_text="Backend policy"),
            tool_boundary=HarnessToolBoundary(registry=ToolRegistry()),
        )
        stream = harness.stream(
            HarnessRequest(
                request_id="cancelled-request",
                user_prompt="User prompt",
            ),
            cancellation_signal=cancellation_signal,
        )
        started = await anext(stream)
        next_event = asyncio.create_task(anext(stream))
        await asyncio.sleep(0)
        cancellation_signal.set()
        stopped = await next_event
        with pytest.raises(StopAsyncIteration):
            await anext(stream)
        return runtime, started, stopped

    runtime, started, stopped = asyncio.run(collect_events())

    assert started == ModelStarted(request_id="cancelled-request")
    assert stopped == ModelStopped(request_id="cancelled-request")
    assert runtime.abort_calls == ("cancelled-request",)


def test_harness_rejects_unexpected_tool_marker_as_bounded_failure() -> None:
    async def collect_events():
        registry = ToolRegistry()
        harness = ApplicationHarness(
            runtime=FakeModelRuntime(tool_request_after_chunks=0),
            policy=HarnessPolicy(application_text="Backend policy"),
            tool_boundary=HarnessToolBoundary(registry=registry),
        )
        events = [
            event
            async for event in harness.stream(
                HarnessRequest(
                    request_id="tool-request",
                    user_prompt="User prompt",
                )
            )
        ]
        return registry, events

    registry, events = asyncio.run(collect_events())

    assert registry.model_tool_descriptions() == ()
    assert events == [
        ModelStarted(request_id="tool-request"),
        ModelFailed(
            request_id="tool-request",
            message="model tool requests are unsupported",
        ),
    ]
    assert not any(isinstance(event, ModelCompleted) for event in events)


def test_harness_structure_has_only_phase_one_orchestration_state() -> None:
    constructor_parameters = signature(ApplicationHarness).parameters
    public_methods = {
        name
        for name, value in vars(ApplicationHarness).items()
        if not name.startswith("_") and callable(value)
    }

    assert set(constructor_parameters) == {"runtime", "policy", "tool_boundary"}
    assert constructor_parameters["runtime"].annotation is ModelRuntime
    assert set(ApplicationHarness.__slots__) == {
        "_runtime",
        "_policy",
        "_tool_boundary",
    }
    assert public_methods == {"stream"}


@pytest.mark.parametrize(
    "forbidden_dependency_or_state",
    ("llama", "httpx", "persona", "conversation", "persistence", "research"),
)
def test_harness_core_excludes_transport_and_later_phase_state(
    forbidden_dependency_or_state: str,
) -> None:
    module_identifiers = tuple(name.casefold() for name in vars(harness_core))

    assert all(
        forbidden_dependency_or_state not in identifier
        for identifier in module_identifiers
    )
