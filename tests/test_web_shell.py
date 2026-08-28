import asyncio
import json
from html.parser import HTMLParser

from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.model_runtime import FakeModelRuntime, RuntimeFailureError


HOSTILE_MODEL_OUTPUT = (
    '<script>window.hostile = true</script>'
    '<img src="x" onerror="window.hostile = true">'
    '<a href="javascript:window.hostile = true">unsafe</a>'
)
HOSTILE_DISPLAYED_ERROR = (
    'Failure near C:\\models\\<unsafe>.gguf: '
    '<img src="x" onerror="window.errorHostile = true">'
    '<script>window.errorHostile = true</script>'
)


class AssetReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        if tag == "link" and attributes.get("href"):
            self.references.append(attributes["href"])
        if tag == "script" and attributes.get("src"):
            self.references.append(attributes["src"])


async def request_local_web_assets():
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://localhost") as client:
        return (
            await client.get("/"),
            await client.get("/static/sampo.css"),
            await client.get("/static/generation.js"),
            await client.get("/static/alpine-3.16.3.min.js"),
        )


def test_local_web_shell_and_stylesheet_are_served() -> None:
    response, stylesheet_response, generation_ui_response, alpine_response = asyncio.run(
        request_local_web_assets()
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<h1>Sampo</h1>" in response.text
    assert "Local AI workspace" in response.text
    assert stylesheet_response.status_code == 200
    assert stylesheet_response.headers["content-type"].startswith("text/css")
    assert "font-family: system-ui" in stylesheet_response.text
    assert generation_ui_response.status_code == 200
    assert generation_ui_response.headers["content-type"].startswith(
        "text/javascript"
    )
    assert "window.sampoGeneration" in generation_ui_response.text
    assert alpine_response.status_code == 200
    assert alpine_response.headers["content-type"].startswith("text/javascript")
    assert len(alpine_response.content) > 50_000


def test_shell_references_only_required_local_assets() -> None:
    response, _, _, _ = asyncio.run(request_local_web_assets())
    parser = AssetReferenceParser()
    parser.feed(response.text)

    assert parser.references == [
        "http://localhost/static/sampo.css",
        "http://localhost/static/generation.js",
        "http://localhost/static/alpine-3.16.3.min.js",
    ]
    assert all(reference.startswith("http://localhost/") for reference in parser.references)


def test_shell_contains_phase_one_prompt_and_send_controls() -> None:
    response, _, _, _ = asyncio.run(request_local_web_assets())

    assert '<textarea\n        id="prompt"' in response.text
    assert 'name="prompt"' in response.text
    assert 'maxlength="15966"' in response.text
    assert '<button type="submit"' in response.text
    assert ">Send</button>" in response.text


def test_shell_uses_small_local_alpine_generation_state() -> None:
    response, _, generation_ui_response, _ = asyncio.run(
        request_local_web_assets()
    )

    assert 'x-data="sampoGeneration()"' in response.text
    assert 'x-model="prompt"' in response.text
    assert "prompt:" in generation_ui_response.text
    assert "generationId:" in generation_ui_response.text
    assert "responseText:" in generation_ui_response.text
    assert "errorText:" in generation_ui_response.text


def test_generation_form_submits_to_backend_with_csrf_token() -> None:
    response, _, generation_ui_response, _ = asyncio.run(
        request_local_web_assets()
    )
    source = generation_ui_response.text

    assert '@submit.prevent="send"' in response.text
    assert 'fetch("/api/generations"' in source
    assert '"X-CSRF-Token": this.csrfToken()' in source
    assert 'body: JSON.stringify({ prompt: this.prompt })' in source
    assert "payload.generation_id" in source
    assert "llama" not in source.casefold()


def test_generation_ui_subscribes_only_to_application_sse_route() -> None:
    _, _, generation_ui_response, _ = asyncio.run(request_local_web_assets())
    source = generation_ui_response.text

    assert "new EventSource(" in source
    assert "`/api/generations/${generationPath}/events`" in source
    assert 'addEventListener("generation.started"' in source
    assert "http://" not in source
    assert "https://" not in source


def test_streamed_assistant_text_uses_only_inert_text_binding() -> None:
    response, _, generation_ui_response, _ = asyncio.run(
        request_local_web_assets()
    )
    markup = response.text
    source = generation_ui_response.text

    assert 'data-assistant-output x-text="responseText"' in markup
    assert 'addEventListener("generation.delta"' in source
    assert "this.responseText += payload.text" in source
    assert "x-html" not in markup
    assert "innerHTML" not in source


def test_generation_ui_presents_all_active_and_terminal_statuses() -> None:
    response, _, generation_ui_response, _ = asyncio.run(
        request_local_web_assets()
    )
    source = generation_ui_response.text

    assert 'data-generation-status x-text="status"' in response.text
    for status in ("streaming", "completed", "stopped", "failed"):
        assert f'"{status}"' in source
    for event_name in (
        "generation.completed",
        "generation.stopped",
        "generation.failed",
    ):
        assert f'addEventListener("{event_name}"' in source


def test_stop_generation_uses_protected_application_cancel_route() -> None:
    response, _, generation_ui_response, _ = asyncio.run(
        request_local_web_assets()
    )
    source = generation_ui_response.text

    assert ">Stop Generation</button>" in response.text
    assert '@click="stopGeneration"' in response.text
    assert "`/api/generations/${generationPath}/cancel`" in source
    assert 'method: "POST"' in source
    assert 'headers: { "X-CSRF-Token": this.csrfToken() }' in source


def test_phase_one_ui_prevents_overlapping_generations() -> None:
    response, _, generation_ui_response, _ = asyncio.run(
        request_local_web_assets()
    )
    source = generation_ui_response.text

    assert ':disabled="isActive"' in response.text
    assert ':disabled="!canSend"' in response.text
    assert "return !this.isActive" in source
    assert "if (!this.canSend)" in source
    assert "this.requestInFlight = true" in source


def test_unavailable_local_runtime_is_presented_as_explicit_ui_failure() -> None:
    response, _, generation_ui_response, _ = asyncio.run(
        request_local_web_assets()
    )
    source = generation_ui_response.text

    assert 'data-generation-error' in response.text
    assert 'x-text="errorText"' in response.text
    assert 'this.status = "failed"' in source
    assert 'payload.detail === "model runtime is not configured"' in source
    assert 'return "Local model runtime is unavailable."' in source


def test_runtime_capability_error_is_presented_from_failed_sse_event() -> None:
    response, _, generation_ui_response, _ = asyncio.run(
        request_local_web_assets()
    )
    source = generation_ui_response.text

    assert 'addEventListener("generation.failed"' in source
    assert 'typeof payload.error === "string"' in source
    assert 'x-text="errorText"' in response.text


def test_failed_ui_state_keeps_already_streamed_partial_text() -> None:
    _, _, generation_ui_response, _ = asyncio.run(request_local_web_assets())
    source = generation_ui_response.text
    finish_source = source.split("finish(status, errorText", maxsplit=1)[1].split(
        "async stopGeneration", maxsplit=1
    )[0]

    assert "this.status = status" in finish_source
    assert "this.errorText = errorText" in finish_source
    assert "responseText" not in finish_source
    assert "Generation stream disconnected." in source


def test_hostile_model_output_reaches_only_inert_text_binding() -> None:
    async def exercise():
        application = create_app(
            model_runtime=FakeModelRuntime(chunks=(HOSTILE_MODEL_OUTPUT,))
        )
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            created = await client.post(
                "/api/generations",
                json={"prompt": "Hostile output fixture"},
                headers={
                    "origin": "http://localhost",
                    "x-csrf-token": application.state.csrf_token,
                },
            )
            generation_id = created.json()["generation_id"]
            streamed = await client.get(
                f"/api/generations/{generation_id}/events",
                headers={"origin": "http://localhost"},
            )
            shell = await client.get("/")
            generation_ui = await client.get("/static/generation.js")
        return streamed, shell, generation_ui

    streamed, shell, generation_ui = asyncio.run(exercise())
    streamed_payloads = [
        json.loads(line.removeprefix("data: "))
        for line in streamed.text.splitlines()
        if line.startswith("data: ")
    ]

    assert any(
        payload.get("text") == HOSTILE_MODEL_OUTPUT
        for payload in streamed_payloads
    )
    assert HOSTILE_MODEL_OUTPUT not in shell.text
    assert 'data-assistant-output x-text="responseText"' in shell.text
    assert "this.responseText += payload.text" in generation_ui.text
    assert "x-html" not in shell.text
    assert "innerHTML" not in generation_ui.text


def test_hostile_error_and_filename_text_reaches_only_inert_binding() -> None:
    async def exercise():
        application = create_app(
            model_runtime=FakeModelRuntime(
                failure=RuntimeFailureError(HOSTILE_DISPLAYED_ERROR),
            )
        )
        service = application.state.generation_service
        state = service.create_generation("Hostile error fixture")
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            streamed = await client.get(
                f"/api/generations/{state.generation_id}/events",
                headers={"origin": "http://localhost"},
            )
            shell = await client.get("/")
            generation_ui = await client.get("/static/generation.js")
        return streamed, shell, generation_ui

    streamed, shell, generation_ui = asyncio.run(exercise())
    streamed_payloads = [
        json.loads(line.removeprefix("data: "))
        for line in streamed.text.splitlines()
        if line.startswith("data: ")
    ]

    assert streamed_payloads[-1]["error"] == HOSTILE_DISPLAYED_ERROR
    assert HOSTILE_DISPLAYED_ERROR not in shell.text
    assert 'data-generation-error' in shell.text
    assert 'x-text="errorText"' in shell.text
    assert "this.errorText = errorText" in generation_ui.text
    assert "x-html" not in shell.text
    assert "innerHTML" not in generation_ui.text


def test_generation_ui_does_not_log_prompt_output_errors_or_csrf() -> None:
    _, _, generation_ui_response, _ = asyncio.run(request_local_web_assets())
    source = generation_ui_response.text

    assert "console." not in source
    assert "localStorage" not in source
    assert "sessionStorage" not in source
