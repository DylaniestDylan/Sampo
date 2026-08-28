import asyncio
import json
import logging

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request

from app.api.generations import (
    MAX_API_PROMPT_CHARS,
    MAX_SSE_EVENT_DATA_BYTES,
    generation_events,
)
from app.harness import (
    ApplicationHarness,
    HarnessPolicy,
    HarnessToolBoundary,
    ToolRegistry,
)
from app.main import create_app
from app.model_runtime import (
    FakeModelRuntime,
    RuntimeCapabilityError,
    RuntimeCancelledError,
    RuntimeFailureError,
)
from app.workspace import (
    MAX_GENERATION_EVENT_TEXT_CHARS,
    SLOW_CONSUMER_ERROR,
    GenerationEventName,
    GenerationRegistry,
    GenerationService,
    GenerationStatus,
)


def _headers(application) -> dict[str, str]:
    return {
        "origin": "http://localhost",
        "x-csrf-token": application.state.csrf_token,
    }


def _service(
    runtime: FakeModelRuntime,
    *,
    registry: GenerationRegistry | None = None,
) -> GenerationService:
    return GenerationService(
        harness=ApplicationHarness(
            runtime=runtime,
            policy=HarnessPolicy(application_text="Backend policy"),
            tool_boundary=HarnessToolBoundary(registry=ToolRegistry()),
        ),
        registry=registry,
    )


def _parse_sse(body: str) -> list[tuple[str, dict[str, str]]]:
    parsed = []
    for block in body.strip().split("\n\n"):
        lines = block.splitlines()
        parsed.append(
            (
                lines[0].removeprefix("event: "),
                json.loads(lines[1].removeprefix("data: ")),
            )
        )
    return parsed


async def _wait_until(predicate, *, attempts: int = 20) -> None:
    for _ in range(attempts):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition did not become true")


def test_post_generation_validates_prompt_and_returns_one_opaque_id() -> None:
    async def exercise():
        application = create_app(model_runtime=FakeModelRuntime())
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            accepted = await client.post(
                "/api/generations",
                json={"prompt": "Hello"},
                headers=_headers(application),
            )
            blank = await client.post(
                "/api/generations",
                json={"prompt": "   "},
                headers=_headers(application),
            )
            oversized = await client.post(
                "/api/generations",
                json={"prompt": "x" * (MAX_API_PROMPT_CHARS + 1)},
                headers=_headers(application),
            )
        return accepted, blank, oversized

    accepted, blank, oversized = asyncio.run(exercise())

    assert accepted.status_code == 202
    assert set(accepted.json()) == {"generation_id"}
    assert len(accepted.json()["generation_id"]) >= 32
    assert blank.status_code == 422
    assert oversized.status_code == 422


def test_generation_route_requires_configured_runtime() -> None:
    async def exercise():
        application = create_app()
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            return await client.post(
                "/api/generations",
                json={"prompt": "Hello"},
                headers=_headers(application),
            )

    response = asyncio.run(exercise())

    assert response.status_code == 503
    assert response.json() == {"detail": "model runtime is not configured"}


def test_backend_generation_service_drives_harness_with_internal_request_id() -> None:
    async def exercise():
        gate = asyncio.Event()
        runtime = FakeModelRuntime(chunks=("response",), chunk_gate=gate)
        service = _service(runtime)
        state = service.create_generation("User prompt")
        assert state.status is GenerationStatus.CREATED
        await asyncio.sleep(0)
        streaming = service.get_generation(state.generation_id)
        gate.set()
        events = [event async for event in service.stream_events(state.generation_id)]
        return (
            runtime,
            state,
            streaming,
            service.get_generation(state.generation_id),
            events,
        )

    runtime, initial, streaming, terminal, events = asyncio.run(exercise())

    assert streaming is not None
    assert streaming.status is GenerationStatus.STREAMING
    assert runtime.stream_requests[0].user_text == "User prompt"
    assert runtime.stream_requests[0].request_id != initial.generation_id
    assert terminal is not None
    assert terminal.status is GenerationStatus.COMPLETED
    assert [event.name for event in events] == [
        GenerationEventName.STARTED,
        GenerationEventName.DELTA,
        GenerationEventName.COMPLETED,
    ]


def test_status_route_returns_bounded_summary_and_unknown_is_explicit() -> None:
    async def exercise():
        application = create_app(model_runtime=FakeModelRuntime())
        service = application.state.generation_service
        created = service.create_generation("Prompt")
        await _wait_until(
            lambda: service.get_generation(created.generation_id).status
            is GenerationStatus.COMPLETED
        )
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            known = await client.get(f"/api/generations/{created.generation_id}")
            unknown = await client.get("/api/generations/not-known")
        return created, known, unknown

    created, known, unknown = asyncio.run(exercise())

    assert known.status_code == 200
    assert known.json() == {
        "generation_id": created.generation_id,
        "status": "completed",
        "error": None,
    }
    assert unknown.status_code == 404
    assert unknown.json() == {"detail": "generation not found"}


def test_cancel_route_rejects_unknown_generation() -> None:
    async def exercise():
        application = create_app(model_runtime=FakeModelRuntime())
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            return await client.post(
                "/api/generations/not-known/cancel",
                headers=_headers(application),
            )

    response = asyncio.run(exercise())

    assert response.status_code == 404
    assert response.json() == {"detail": "generation not found"}


def test_cancel_route_enforces_host_origin_and_csrf_policy() -> None:
    async def exercise():
        gate = asyncio.Event()
        application = create_app(
            model_runtime=FakeModelRuntime(chunks=("blocked",), chunk_gate=gate)
        )
        service = application.state.generation_service
        generation_ids = [
            service.create_generation("Prompt").generation_id for _ in range(4)
        ]
        await asyncio.sleep(0)
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            bad_host = await client.post(
                f"/api/generations/{generation_ids[0]}/cancel",
                headers={
                    "host": "unrelated.example",
                    "origin": "http://unrelated.example",
                    "x-csrf-token": application.state.csrf_token,
                },
            )
            bad_origin = await client.post(
                f"/api/generations/{generation_ids[1]}/cancel",
                headers={
                    "origin": "https://unrelated.example",
                    "x-csrf-token": application.state.csrf_token,
                },
            )
            bad_csrf = await client.post(
                f"/api/generations/{generation_ids[2]}/cancel",
                headers={
                    "origin": "http://localhost",
                    "x-csrf-token": "not-the-token",
                },
            )
            accepted = await client.post(
                f"/api/generations/{generation_ids[3]}/cancel",
                headers=_headers(application),
            )
        for generation_id in generation_ids[:3]:
            await service.cancel_generation(generation_id)
        return bad_host, bad_origin, bad_csrf, accepted

    bad_host, bad_origin, bad_csrf, accepted = asyncio.run(exercise())

    assert bad_host.status_code == 400
    assert bad_host.text == "Invalid host header"
    assert bad_origin.status_code == 403
    assert bad_origin.text == "Origin not allowed"
    assert bad_csrf.status_code == 403
    assert bad_csrf.text == "Invalid CSRF token"
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "stopped"


def test_api_cancellation_reaches_internal_runtime_request_and_stops_task() -> None:
    async def exercise():
        gate = asyncio.Event()
        runtime = FakeModelRuntime(
            chunks=("late runtime chunk",),
            chunk_gate=gate,
        )
        application = create_app(model_runtime=runtime)
        service = application.state.generation_service
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            created = await client.post(
                "/api/generations",
                json={"prompt": "Prompt"},
                headers=_headers(application),
            )
            generation_id = created.json()["generation_id"]
            await _wait_until(lambda: bool(runtime.stream_requests))
            runtime_request_id = runtime.stream_requests[0].request_id
            cancelled = await client.post(
                f"/api/generations/{generation_id}/cancel",
                headers=_headers(application),
            )
            repeated = await client.post(
                f"/api/generations/{generation_id}/cancel",
                headers=_headers(application),
            )
            status_response = await client.get(
                f"/api/generations/{generation_id}"
            )
            streamed = await client.get(
                f"/api/generations/{generation_id}/events",
                headers={"origin": "http://localhost"},
            )
            await asyncio.sleep(0)
            task_remains = generation_id in service._tasks
        return (
            generation_id,
            runtime_request_id,
            cancelled,
            repeated,
            status_response,
            streamed,
            runtime,
            task_remains,
        )

    (
        generation_id,
        runtime_request_id,
        cancelled,
        repeated,
        status_response,
        streamed,
        runtime,
        task_remains,
    ) = asyncio.run(exercise())
    events = _parse_sse(streamed.text)

    assert runtime_request_id != generation_id
    assert runtime.abort_calls == (runtime_request_id,)
    assert cancelled.status_code == repeated.status_code == 200
    assert cancelled.json() == repeated.json() == status_response.json()
    assert cancelled.json() == {
        "generation_id": generation_id,
        "status": "stopped",
        "error": None,
    }
    assert events[-1][0] == "generation.stopped"
    assert all(
        event_name in {"generation.started", "generation.stopped"}
        for event_name, _ in events
    )
    assert "late runtime chunk" not in streamed.text
    assert "generation.completed" not in streamed.text
    assert not task_remains


def test_real_sse_route_streams_application_owned_events_to_terminal() -> None:
    async def exercise():
        application = create_app(
            model_runtime=FakeModelRuntime(chunks=("Hello, ", "world"))
        )
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            created = await client.post(
                "/api/generations",
                json={"prompt": "Prompt"},
                headers=_headers(application),
            )
            generation_id = created.json()["generation_id"]
            streamed = await client.get(
                f"/api/generations/{generation_id}/events",
                headers={"origin": "http://localhost"},
            )
        return generation_id, streamed

    generation_id, response = asyncio.run(exercise())
    events = _parse_sse(response.text)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert [event_name for event_name, _ in events] == [
        "generation.started",
        "generation.delta",
        "generation.delta",
        "generation.completed",
    ]
    assert "".join(data.get("text", "") for _, data in events) == "Hello, world"
    assert all(data["generation_id"] == generation_id for _, data in events)
    assert all("request_id" not in data for _, data in events)
    assert "llama" not in response.text.casefold()


@pytest.mark.parametrize(
    ("failure", "expected_event", "expected_status"),
    [
        (None, "generation.completed", GenerationStatus.COMPLETED),
        (
            RuntimeFailureError("local runtime failed"),
            "generation.failed",
            GenerationStatus.FAILED,
        ),
        (
            RuntimeCancelledError("local runtime stopped"),
            "generation.stopped",
            GenerationStatus.STOPPED,
        ),
    ],
)
def test_sse_always_sends_truthful_terminal_event(
    failure, expected_event: str, expected_status: GenerationStatus
) -> None:
    async def exercise():
        runtime = FakeModelRuntime(
            chunks=("partial",),
            failure=failure,
            failure_after_chunks=1,
        )
        application = create_app(model_runtime=runtime)
        service = application.state.generation_service
        state = service.create_generation("Prompt")
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            response = await client.get(
                f"/api/generations/{state.generation_id}/events",
                headers={"origin": "http://localhost"},
            )
        return service.get_generation(state.generation_id), response

    state, response = asyncio.run(exercise())
    events = _parse_sse(response.text)

    assert state is not None
    assert state.status is expected_status
    assert events[-1][0] == expected_event
    assert sum(
        event_name
        in {
            "generation.completed",
            "generation.stopped",
            "generation.failed",
        }
        for event_name, _ in events
    ) == 1


def test_incompatible_runtime_capability_is_an_explicit_failed_event() -> None:
    error = "selected local model does not support text chat"

    async def exercise():
        application = create_app(
            model_runtime=FakeModelRuntime(
                failure=RuntimeCapabilityError(error),
            )
        )
        service = application.state.generation_service
        state = service.create_generation("Prompt")
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            response = await client.get(
                f"/api/generations/{state.generation_id}/events",
                headers={"origin": "http://localhost"},
            )
        return service.get_generation(state.generation_id), response

    state, response = asyncio.run(exercise())
    events = _parse_sse(response.text)

    assert state is not None
    assert state.status is GenerationStatus.FAILED
    assert events[-1] == (
        "generation.failed",
        {
            "generation_id": state.generation_id,
            "error": error,
        },
    )
    assert "generation.completed" not in response.text


def test_midstream_failure_preserves_partial_text_as_incomplete() -> None:
    error = "local runtime failed after partial output"

    async def exercise():
        application = create_app(
            model_runtime=FakeModelRuntime(
                chunks=("partial answer", "must not appear"),
                failure=RuntimeFailureError(error),
                failure_after_chunks=1,
            )
        )
        service = application.state.generation_service
        state = service.create_generation("Prompt")
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            response = await client.get(
                f"/api/generations/{state.generation_id}/events",
                headers={"origin": "http://localhost"},
            )
        return service.get_generation(state.generation_id), response

    state, response = asyncio.run(exercise())
    events = _parse_sse(response.text)

    assert state is not None
    assert state.status is GenerationStatus.FAILED
    assert [name for name, _ in events] == [
        "generation.started",
        "generation.delta",
        "generation.failed",
    ]
    assert events[1][1]["text"] == "partial answer"
    assert events[-1][1]["error"] == error
    assert "must not appear" not in response.text
    assert "generation.completed" not in response.text


def test_default_operational_logs_exclude_csrf_prompt_and_output(
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret_prompt = "PROMPT_SECRET_1ff190af"
    secret_output = "OUTPUT_SECRET_b0445da3"
    caplog.set_level(logging.DEBUG)

    async def exercise():
        application = create_app(
            model_runtime=FakeModelRuntime(chunks=(secret_output,))
        )
        csrf_token = application.state.csrf_token
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            created = await client.post(
                "/api/generations",
                json={"prompt": secret_prompt},
                headers={
                    "origin": "http://localhost",
                    "x-csrf-token": csrf_token,
                },
            )
            generation_id = created.json()["generation_id"]
            streamed = await client.get(
                f"/api/generations/{generation_id}/events",
                headers={"origin": "http://localhost"},
            )
        return csrf_token, created, streamed

    csrf_token, created, streamed = asyncio.run(exercise())

    assert created.status_code == 202
    assert streamed.status_code == 200
    assert secret_prompt not in caplog.text
    assert secret_output not in caplog.text
    assert csrf_token not in caplog.text


def test_large_runtime_delta_is_split_into_bounded_sse_payloads() -> None:
    text = "λ" * (MAX_GENERATION_EVENT_TEXT_CHARS + 1)

    async def exercise():
        application = create_app(model_runtime=FakeModelRuntime(chunks=(text,)))
        service = application.state.generation_service
        state = service.create_generation("Prompt")
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            return await client.get(
                f"/api/generations/{state.generation_id}/events",
                headers={"origin": "http://localhost"},
            )

    response = asyncio.run(exercise())
    events = _parse_sse(response.text)
    delta_blocks = response.text.split("\n\n")[1:3]

    assert "".join(data.get("text", "") for _, data in events) == text
    assert all(
        len(block.splitlines()[1].removeprefix("data: ").encode("utf-8"))
        <= MAX_SSE_EVENT_DATA_BYTES
        for block in delta_blocks
    )


def test_unknown_generation_sse_route_is_explicit() -> None:
    async def exercise():
        application = create_app(model_runtime=FakeModelRuntime())
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            return await client.get(
                "/api/generations/not-known/events",
                headers={"origin": "http://localhost"},
            )

    response = asyncio.run(exercise())

    assert response.status_code == 404
    assert response.json() == {"detail": "generation not found"}


def test_slow_consumer_fails_generation_without_unbounded_backlog() -> None:
    async def exercise():
        runtime = FakeModelRuntime(chunks=("one", "two", "three"))
        registry = GenerationRegistry(event_buffer_capacity=2)
        service = _service(runtime, registry=registry)
        created = service.create_generation("Prompt")
        await _wait_until(
            lambda: service.get_generation(created.generation_id).status
            is GenerationStatus.FAILED
        )
        state = service.get_generation(created.generation_id)
        buffer = registry.event_buffer(created.generation_id)
        events = [event async for event in service.stream_events(created.generation_id)]
        return state, buffer, events

    state, buffer, events = asyncio.run(exercise())

    assert state is not None
    assert state.status is GenerationStatus.FAILED
    assert state.error == SLOW_CONSUMER_ERROR
    assert buffer is not None
    assert buffer.size <= buffer.capacity
    assert [event.name for event in events] == [GenerationEventName.FAILED]


def test_full_buffer_at_completion_is_reported_as_slow_consumer_failure() -> None:
    async def exercise():
        runtime = FakeModelRuntime(chunks=("one", "two"))
        registry = GenerationRegistry(event_buffer_capacity=3)
        service = _service(runtime, registry=registry)
        created = service.create_generation("Prompt")
        task = service._tasks[created.generation_id]
        await task
        state = service.get_generation(created.generation_id)
        events = [event async for event in service.stream_events(created.generation_id)]
        return state, events

    state, events = asyncio.run(exercise())

    assert state is not None
    assert state.status is GenerationStatus.FAILED
    assert state.error == SLOW_CONSUMER_ERROR
    assert [event.name for event in events] == [GenerationEventName.FAILED]


def test_closing_real_sse_route_stops_still_active_ephemeral_generation() -> None:
    async def exercise():
        gate = asyncio.Event()
        runtime = FakeModelRuntime(chunks=("unreached",), chunk_gate=gate)
        application = create_app(model_runtime=runtime)
        service = application.state.generation_service
        created = service.create_generation("Prompt")
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "scheme": "http",
                "path": f"/api/generations/{created.generation_id}/events",
                "headers": [],
                "app": application,
            }
        )
        response = await generation_events(created.generation_id, request)
        iterator = response.body_iterator
        first = await anext(iterator)
        await iterator.aclose()
        await asyncio.sleep(0)
        return first, service.get_generation(created.generation_id), runtime

    first, state, runtime = asyncio.run(exercise())

    assert "event: generation.started" in first
    assert state is not None
    assert state.status is GenerationStatus.STOPPED
    assert runtime.abort_calls == (runtime.stream_requests[0].request_id,)


def test_real_sse_route_enforces_host_and_origin_policy() -> None:
    async def exercise():
        application = create_app(model_runtime=FakeModelRuntime())
        service = application.state.generation_service
        first = service.create_generation("First")
        second = service.create_generation("Second")
        third = service.create_generation("Third")
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            bad_host = await client.get(
                f"/api/generations/{first.generation_id}/events",
                headers={
                    "host": "unrelated.example",
                    "origin": "http://unrelated.example",
                },
            )
            bad_origin = await client.get(
                f"/api/generations/{second.generation_id}/events",
                headers={"origin": "https://unrelated.example"},
            )
            accepted = await client.get(
                f"/api/generations/{third.generation_id}/events",
                headers={"origin": "http://localhost"},
            )
        return bad_host, bad_origin, accepted

    bad_host, bad_origin, accepted = asyncio.run(exercise())

    assert bad_host.status_code == 400
    assert bad_host.text == "Invalid host header"
    assert bad_origin.status_code == 403
    assert bad_origin.text == "Origin not allowed"
    assert accepted.status_code == 200
    assert "event: generation.completed" in accepted.text
    assert "access-control-allow-origin" not in accepted.headers
