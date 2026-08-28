import asyncio
from dataclasses import fields
from inspect import signature

import pytest

from app.harness import (
    HarnessToolBoundary,
    ToolRegistry,
    UnexpectedModelToolRequestError,
)
from app.model_runtime import (
    LlamaCppModelRuntime,
    ModelCompleted,
    ModelStarted,
    ModelToolRequest,
    RuntimeCapabilities,
    RuntimeCancelledError,
    RuntimeConfigurationError,
    RuntimeFailureError,
    RuntimeUnavailableError,
)
from app.model_runtime.llama_cpp import _request_payload
from app.model_runtime.llama_cpp import (
    _TransportConnectionError,
    _TransportHttpError,
)
from app.model_runtime.request import ModelRequest
from tests.runtime_contract import ModelRuntimeContract


class MockLlamaCppTransport:
    def __init__(
        self,
        *,
        health: object = None,
        lines: tuple[str, ...] = (),
        line_gate: asyncio.Event | None = None,
        probe_failure: Exception | None = None,
        stream_failure: Exception | None = None,
        stream_failure_after_lines: int = 0,
    ) -> None:
        self.health = {"status": "ok"} if health is None else health
        self.lines = lines
        self.probe_calls = 0
        self.stream_calls: list[tuple[str, dict[str, object]]] = []
        self.abort_calls: list[str] = []
        self.line_gate = line_gate
        self.probe_failure = probe_failure
        self.stream_failure = stream_failure
        self.stream_failure_after_lines = stream_failure_after_lines

    async def probe_health(self) -> object:
        self.probe_calls += 1
        if self.probe_failure is not None:
            raise self.probe_failure
        return self.health

    async def stream_lines(self, *, request_id: str, payload: dict[str, object]):
        self.stream_calls.append((request_id, payload))
        if self.stream_failure is not None and self.stream_failure_after_lines == 0:
            raise self.stream_failure
        for index, line in enumerate(self.lines, start=1):
            if self.line_gate is not None:
                await self.line_gate.wait()
            yield line
            if (
                self.stream_failure is not None
                and index == self.stream_failure_after_lines
            ):
                raise self.stream_failure

    async def abort(self, request_id: str) -> None:
        self.abort_calls.append(request_id)
        if self.line_gate is not None:
            self.line_gate.set()


def make_runtime(transport: MockLlamaCppTransport) -> LlamaCppModelRuntime:
    return LlamaCppModelRuntime(
        endpoint="http://127.0.0.1:8080",
        model="test-model",
        transport=transport,
    )


class TestLlamaCppModelRuntimeContract(ModelRuntimeContract):
    expected_text = "Contract response"

    def create_runtime(self) -> LlamaCppModelRuntime:
        return make_runtime(
            MockLlamaCppTransport(
                lines=(
                    'data: {"choices":[{"delta":{"content":"Contract "}}]}',
                    'data: {"choices":[{"delta":{"content":"response"}}]}',
                    "data: [DONE]",
                )
            )
        )


def test_llama_cpp_runtime_normalizes_capability_probe() -> None:
    transport = MockLlamaCppTransport()

    capabilities = asyncio.run(make_runtime(transport).get_capabilities())

    assert capabilities == RuntimeCapabilities(
        available=True,
        text_chat=True,
        streaming=True,
    )
    assert transport.probe_calls == 1


@pytest.mark.parametrize("health", [{"status": "loading"}, {}, [], "ok"])
def test_llama_cpp_runtime_rejects_invalid_health_response(health: object) -> None:
    with pytest.raises(RuntimeUnavailableError, match="invalid health response"):
        asyncio.run(make_runtime(MockLlamaCppTransport(health=health)).get_capabilities())


def test_llama_cpp_runtime_rejects_remote_endpoint_even_when_directly_created() -> None:
    with pytest.raises(RuntimeConfigurationError, match="numeric loopback IP"):
        LlamaCppModelRuntime(
            endpoint="https://cloud-model.example/v1",
            model="remote-model",
            transport=MockLlamaCppTransport(),
        )


def test_llama_cpp_request_translation_stays_transport_internal() -> None:
    request = ModelRequest(
        request_id="sampo-request-1",
        system_text="Trusted application policy",
        user_text="User prompt",
        max_output_tokens=321,
    )

    assert _request_payload(request, configured_model="configured-model") == {
        "model": "configured-model",
        "messages": [
            {"role": "system", "content": "Trusted application policy"},
            {"role": "user", "content": "User prompt"},
        ],
        "max_tokens": 321,
        "stream": True,
    }


def test_llama_cpp_request_translation_uses_explicit_local_model_override() -> None:
    request = ModelRequest(
        request_id="sampo-request-1",
        system_text="Trusted application policy",
        user_text="User prompt",
        model="explicit-local-model",
    )

    payload = _request_payload(request, configured_model="configured-model")

    assert payload["model"] == "explicit-local-model"


def test_llama_cpp_runtime_translates_stream_to_application_events() -> None:
    async def collect_events():
        transport = MockLlamaCppTransport(
            lines=(
                'data: {"choices":[{"delta":{"role":"assistant"}}]}',
                'data: {"choices":[{"delta":{"content":"Hello "}}]}',
                'data: {"choices":[{"delta":{"content":"locally"}}]}',
                "data: [DONE]",
            )
        )
        runtime = make_runtime(transport)
        request = ModelRequest(
            request_id="sampo-request-1",
            system_text="Trusted application policy",
            user_text="User prompt",
        )
        events = [event async for event in runtime.stream_chat(request)]
        return events, transport

    events, transport = asyncio.run(collect_events())

    assert [type(event).__name__ for event in events] == [
        "ModelStarted",
        "ModelDelta",
        "ModelDelta",
        "ModelCompleted",
    ]
    assert [getattr(event, "text", None) for event in events] == [
        None,
        "Hello ",
        "locally",
        None,
    ]
    assert transport.stream_calls[0][0] == "sampo-request-1"


def test_llama_cpp_runtime_preserves_structured_tool_request_without_completion() -> None:
    async def collect_events():
        runtime = make_runtime(
            MockLlamaCppTransport(
                lines=(
                    'data: {"choices":[{"delta":{"tool_calls":[{"id":"call-1",'
                    '"function":{"name":"filesystem.read",'
                    '"arguments":"unbounded model arguments"}}]}}]}',
                    "data: [DONE]",
                )
            )
        )
        request = ModelRequest(
            request_id="unexpected-tool-request",
            system_text="Trusted application policy",
            user_text="User prompt",
        )
        return [event async for event in runtime.stream_chat(request)]

    events = asyncio.run(collect_events())

    assert [type(event) for event in events] == [ModelStarted, ModelToolRequest]
    assert events[-1] == ModelToolRequest(request_id="unexpected-tool-request")
    assert not any(isinstance(event, ModelCompleted) for event in events)
    assert {field.name for field in fields(events[-1])} == {"request_id"}
    with pytest.raises(UnexpectedModelToolRequestError) as raised:
        HarnessToolBoundary(registry=ToolRegistry()).reject_model_tool_request(
            events[-1]
        )
    assert raised.value.code == "unsupported_model_tool_request"
    assert str(raised.value) == "model tool requests are unsupported"


def test_llama_cpp_runtime_aborts_by_sampo_request_id() -> None:
    async def exercise_cancellation():
        gate = asyncio.Event()
        transport = MockLlamaCppTransport(
            lines=('data: {"choices":[{"delta":{"content":"late"}}]}',),
            line_gate=gate,
        )
        runtime = make_runtime(transport)
        request = ModelRequest(
            request_id="sampo-request-to-cancel",
            system_text="Trusted application policy",
            user_text="User prompt",
        )
        stream = runtime.stream_chat(request)
        await anext(stream)
        pending_chunk = asyncio.ensure_future(anext(stream))
        await asyncio.sleep(0)

        await runtime.abort("sampo-request-to-cancel")

        with pytest.raises(RuntimeCancelledError):
            await pending_chunk
        return transport

    transport = asyncio.run(exercise_cancellation())

    assert transport.abort_calls == ["sampo-request-to-cancel"]


def test_llama_cpp_runtime_normalizes_probe_connection_failure() -> None:
    transport = MockLlamaCppTransport(probe_failure=_TransportConnectionError())

    with pytest.raises(RuntimeUnavailableError, match="runtime is unavailable"):
        asyncio.run(make_runtime(transport).get_capabilities())


def test_llama_cpp_runtime_normalizes_stream_http_failure() -> None:
    async def collect_events():
        runtime = make_runtime(
            MockLlamaCppTransport(stream_failure=_TransportHttpError(503))
        )
        request = ModelRequest(
            request_id="sampo-request-1",
            system_text="Trusted application policy",
            user_text="User prompt",
        )
        return [event async for event in runtime.stream_chat(request)]

    with pytest.raises(RuntimeFailureError, match="HTTP 503"):
        asyncio.run(collect_events())


@pytest.mark.parametrize(
    "lines",
    [
        ("not-an-sse-line",),
        ("data: not-json",),
        ('data: {"choices":[]}',),
        ('data: {"choices":[{"delta":{"content":""}}]}',),
        ('data: {"choices":[{"delta":{"content":"partial"}}]}',),
    ],
)
def test_llama_cpp_runtime_rejects_malformed_stream(
    lines: tuple[str, ...],
) -> None:
    async def collect_events():
        runtime = make_runtime(MockLlamaCppTransport(lines=lines))
        request = ModelRequest(
            request_id="malformed-request",
            system_text="Trusted application policy",
            user_text="User prompt",
        )
        return [event async for event in runtime.stream_chat(request)]

    with pytest.raises(RuntimeFailureError, match="malformed|before completion"):
        asyncio.run(collect_events())


def test_llama_cpp_runtime_normalizes_non_object_delta_as_runtime_failure() -> None:
    async def collect_events():
        runtime = make_runtime(
            MockLlamaCppTransport(
                lines=('data: {"choices":[{"delta":null}]}',)
            )
        )
        request = ModelRequest(
            request_id="malformed-delta-request",
            system_text="Trusted application policy",
            user_text="User prompt",
        )
        return [event async for event in runtime.stream_chat(request)]

    with pytest.raises(RuntimeFailureError, match="malformed") as raised:
        asyncio.run(collect_events())

    assert raised.value.code.value == "runtime_failure"


def test_llama_cpp_runtime_normalizes_mid_stream_disconnect() -> None:
    async def exercise_disconnect():
        runtime = make_runtime(
            MockLlamaCppTransport(
                lines=('data: {"choices":[{"delta":{"content":"partial"}}]}',),
                stream_failure=_TransportConnectionError(),
                stream_failure_after_lines=1,
            )
        )
        request = ModelRequest(
            request_id="disconnect-request",
            system_text="Trusted application policy",
            user_text="User prompt",
        )
        stream = runtime.stream_chat(request)
        started = await anext(stream)
        delta = await anext(stream)
        with pytest.raises(RuntimeFailureError, match="connection failed") as raised:
            await anext(stream)
        return started, delta, raised.value

    started, delta, failure = asyncio.run(exercise_disconnect())

    assert type(started).__name__ == "ModelStarted"
    assert getattr(delta, "text", None) == "partial"
    assert failure.code.value == "runtime_failure"


def test_llama_cpp_failure_does_not_retry_or_select_remote_cloud_fallback() -> None:
    async def exercise_failure():
        transport = MockLlamaCppTransport(
            stream_failure=_TransportConnectionError()
        )
        runtime = make_runtime(transport)
        request = ModelRequest(
            request_id="no-fallback-request",
            system_text="Trusted application policy",
            user_text="Private local prompt",
        )
        with pytest.raises(RuntimeFailureError, match="connection failed"):
            _ = [event async for event in runtime.stream_chat(request)]
        return transport

    transport = asyncio.run(exercise_failure())

    assert len(transport.stream_calls) == 1
    request_id, payload = transport.stream_calls[0]
    assert request_id == "no-fallback-request"
    assert payload["model"] == "test-model"
    assert set(signature(LlamaCppModelRuntime).parameters) == {
        "endpoint",
        "model",
        "timeout_seconds",
        "transport",
    }
