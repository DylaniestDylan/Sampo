import asyncio
import json
from html.parser import HTMLParser
from ipaddress import ip_address
from urllib.parse import urlsplit

import pytest
from httpx import ASGITransport, AsyncClient

from app.harness import (
    ApplicationHarness,
    HarnessPolicy,
    HarnessRequest,
    HarnessToolBoundary,
    ToolRegistry,
)
from app.main import create_app
from app.model_runtime import (
    FakeModelRuntime,
    ModelCompleted,
    ModelFailed,
    RuntimeFailureError,
)
from app.settings import ApplicationSettings
from app.workspace import GenerationStatus


class _AssetReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        href = attributes.get("href")
        source = attributes.get("src")
        if tag == "link" and href is not None:
            self.references.append(href)
        if tag == "script" and source is not None:
            self.references.append(source)


def _protected_headers(application) -> dict[str, str]:
    return {
        "origin": "http://localhost",
        "x-csrf-token": application.state.csrf_token,
    }


async def _wait_until(predicate, *, attempts: int = 20) -> None:
    for _ in range(attempts):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition did not become true")


def test_p01_16_01_default_application_configuration_is_loopback_only() -> None:
    settings = ApplicationSettings(bind_port=8000)
    runtime_host = urlsplit(settings.runtime_endpoint).hostname

    assert ip_address(settings.bind_host).is_loopback
    assert runtime_host is not None
    assert ip_address(runtime_host).is_loopback


@pytest.mark.parametrize(
    "runtime_endpoint",
    (
        "https://cloud-model.example/v1",
        "http://203.0.113.10:8080",
        "http://192.168.1.10:8080",
    ),
)
def test_p01_16_02_remote_runtime_configuration_is_rejected(
    runtime_endpoint: str,
) -> None:
    with pytest.raises(ValueError, match="numeric loopback IP"):
        ApplicationSettings(bind_port=8000, runtime_endpoint=runtime_endpoint)


def test_p01_16_03_unrelated_origin_cannot_invoke_state_changing_api() -> None:
    async def exercise():
        application = create_app(model_runtime=FakeModelRuntime())
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            return await client.post(
                "/api/generations",
                json={"prompt": "must not run"},
                headers={
                    "origin": "https://unrelated.example",
                    "x-csrf-token": application.state.csrf_token,
                },
            )

    response = asyncio.run(exercise())

    assert response.status_code == 403
    assert response.text == "Origin not allowed"
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    "host", ("unrelated.example", "192.168.1.10:8000", "localhost.example")
)
def test_p01_16_04_invalid_local_web_hosts_are_rejected(host: str) -> None:
    async def exercise():
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            return await client.get("/health", headers={"host": host})

    response = asyncio.run(exercise())

    assert response.status_code == 400
    assert response.text == "Invalid host header"


def test_p01_16_05_required_frontend_assets_do_not_use_third_party_cdns() -> None:
    async def exercise():
        transport = ASGITransport(app=create_app())
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            return await client.get("/")

    response = asyncio.run(exercise())
    parser = _AssetReferenceParser()
    parser.feed(response.text)

    assert {urlsplit(reference).path for reference in parser.references} == {
        "/static/sampo.css",
        "/static/generation.js",
        "/static/alpine-3.16.3.min.js",
    }
    assert all(
        urlsplit(reference).scheme == "http"
        and urlsplit(reference).hostname == "localhost"
        for reference in parser.references
    )


def test_p01_16_06_model_facing_tools_remain_empty() -> None:
    registry = ToolRegistry()
    boundary = HarnessToolBoundary(registry=registry)

    assert registry.model_tool_descriptions() == ()
    assert boundary.model_tool_descriptions() == ()


def test_p01_16_07_unexpected_tool_request_fails_closed() -> None:
    async def exercise():
        harness = ApplicationHarness(
            runtime=FakeModelRuntime(tool_request_after_chunks=0),
            policy=HarnessPolicy(application_text="Backend policy"),
            tool_boundary=HarnessToolBoundary(registry=ToolRegistry()),
        )
        return [
            event
            async for event in harness.stream(
                HarnessRequest(
                    request_id="unexpected-tool", user_prompt="User prompt"
                )
            )
        ]

    events = asyncio.run(exercise())

    assert events[-1] == ModelFailed(
        request_id="unexpected-tool",
        message="model tool requests are unsupported",
    )
    assert not any(isinstance(event, ModelCompleted) for event in events)


def test_p01_16_08_runtime_failure_does_not_select_another_model() -> None:
    async def exercise():
        runtime = FakeModelRuntime(
            failure=RuntimeFailureError("configured local runtime failed")
        )
        harness = ApplicationHarness(
            runtime=runtime,
            policy=HarnessPolicy(application_text="Backend policy"),
            tool_boundary=HarnessToolBoundary(registry=ToolRegistry()),
        )
        events = [
            event
            async for event in harness.stream(
                HarnessRequest(
                    request_id="runtime-failure", user_prompt="Private prompt"
                )
            )
        ]
        return runtime, events

    exercised_runtime, emitted_events = asyncio.run(exercise())

    assert len(exercised_runtime.stream_requests) == 1
    assert exercised_runtime.stream_requests[0].model is None
    assert emitted_events[-1] == ModelFailed(
        request_id="runtime-failure",
        message="configured local runtime failed",
    )
    assert not any(
        isinstance(event, ModelCompleted) for event in emitted_events
    )


def test_p01_16_09_cancellation_produces_stopped_and_terminates_work() -> None:
    async def exercise():
        gate = asyncio.Event()
        runtime = FakeModelRuntime(chunks=("late output",), chunk_gate=gate)
        application = create_app(model_runtime=runtime)
        service = application.state.generation_service
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            created = await client.post(
                "/api/generations",
                json={"prompt": "Cancel this work"},
                headers=_protected_headers(application),
            )
            generation_id = created.json()["generation_id"]
            await _wait_until(lambda: bool(runtime.stream_requests))
            stopped = await client.post(
                f"/api/generations/{generation_id}/cancel",
                headers=_protected_headers(application),
            )
            await asyncio.sleep(0)
        return generation_id, stopped, runtime, service

    generated_id, stopped_response, exercised_runtime, generation_service = (
        asyncio.run(exercise())
    )
    state = generation_service.get_generation(generated_id)

    assert stopped_response.json()["status"] == "stopped"
    assert state is not None and state.status is GenerationStatus.STOPPED
    assert exercised_runtime.abort_calls == (
        exercised_runtime.stream_requests[0].request_id,
    )
    assert generated_id not in generation_service._tasks


def test_p01_16_10_unsafe_model_html_is_not_rendered_as_trusted_markup() -> None:
    hostile_output = (
        '<script>window.hostile = true</script>'
        '<img src="x" onerror="window.hostile = true">'
    )

    async def exercise():
        application = create_app(
            model_runtime=FakeModelRuntime(chunks=(hostile_output,))
        )
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            created = await client.post(
                "/api/generations",
                json={"prompt": "Hostile model output fixture"},
                headers=_protected_headers(application),
            )
            generation_id = created.json()["generation_id"]
            streamed = await client.get(
                f"/api/generations/{generation_id}/events",
                headers={"origin": "http://localhost"},
            )
            shell = await client.get("/")
            frontend = await client.get("/static/generation.js")
        return streamed, shell, frontend

    stream_response, shell_response, frontend_response = asyncio.run(exercise())
    payloads = [
        json.loads(line.removeprefix("data: "))
        for line in stream_response.text.splitlines()
        if line.startswith("data: ")
    ]

    assert any(payload.get("text") == hostile_output for payload in payloads)
    assert hostile_output not in shell_response.text
    assert (
        'data-assistant-output x-text="responseText"' in shell_response.text
    )
    assert "this.responseText += payload.text" in frontend_response.text
    assert "x-html" not in shell_response.text
    assert "innerHTML" not in frontend_response.text
