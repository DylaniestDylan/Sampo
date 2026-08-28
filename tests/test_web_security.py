import asyncio
import re

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.responses import Response

from app.main import create_app
from app.web.security import is_same_origin


async def request_health_with_host(host: str):
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://localhost") as client:
        return await client.get("/health", headers={"host": host})


async def request_shell_with_app(application):
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://localhost") as client:
        return await client.get("/")


async def request_test_mutation(headers: dict[str, str]):
    application = create_app()

    @application.post("/api/test-mutation")
    async def test_mutation() -> dict[str, str]:
        return {"status": "accepted"}

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://localhost") as client:
        response = await client.post("/api/test-mutation", headers=headers)
    return application, response


@pytest.mark.parametrize(
    "host",
    ["localhost", "localhost:8000", "127.0.0.1", "127.0.0.1:8000", "[::1]:8000"],
)
def test_trusted_local_hosts_are_allowed(host: str) -> None:
    response = asyncio.run(request_health_with_host(host))

    assert response.status_code == 200


@pytest.mark.parametrize(
    "host",
    ["example.com", "192.168.1.10:8000", "localhost.example", "evil@localhost"],
)
def test_untrusted_hosts_are_rejected(host: str) -> None:
    response = asyncio.run(request_health_with_host(host))

    assert response.status_code == 400
    assert response.text == "Invalid host header"


@pytest.mark.parametrize(
    ("origin", "request_scheme", "request_host"),
    [
        ("http://localhost", "http", "localhost"),
        ("http://localhost:8000", "http", "localhost:8000"),
        ("http://127.0.0.1:8000", "http", "127.0.0.1:8000"),
        ("http://[::1]:8000", "http", "[::1]:8000"),
    ],
)
def test_same_origin_helper_accepts_matching_local_origins(
    origin: str, request_scheme: str, request_host: str
) -> None:
    assert is_same_origin(
        origin, request_scheme=request_scheme, request_host=request_host
    )


@pytest.mark.parametrize(
    "origin",
    [
        None,
        "null",
        "https://localhost:8000",
        "http://localhost:9000",
        "http://example.com:8000",
        "http://evil@localhost:8000",
    ],
)
def test_same_origin_helper_rejects_missing_or_unrelated_origins(
    origin: str | None,
) -> None:
    assert not is_same_origin(
        origin, request_scheme="http", request_host="localhost:8000"
    )


def test_rendered_page_contains_application_issued_csrf_token() -> None:
    application = create_app()
    response = asyncio.run(request_shell_with_app(application))
    match = re.search(r'<meta name="csrf-token" content="([^"]+)">', response.text)

    assert match is not None
    assert match.group(1) == application.state.csrf_token
    assert len(application.state.csrf_token) >= 32
    assert application.state.csrf_token != create_app().state.csrf_token


def test_state_changing_api_rejects_missing_csrf_token() -> None:
    _, response = asyncio.run(
        request_test_mutation({"origin": "http://localhost"})
    )

    assert response.status_code == 403
    assert response.text == "Invalid CSRF token"


def test_state_changing_api_rejects_invalid_csrf_token() -> None:
    _, response = asyncio.run(
        request_test_mutation(
            {"origin": "http://localhost", "x-csrf-token": "not-the-token"}
        )
    )

    assert response.status_code == 403
    assert response.text == "Invalid CSRF token"


def test_state_changing_api_accepts_valid_csrf_token() -> None:
    async def make_request():
        application = create_app()

        @application.post("/api/test-mutation")
        async def test_mutation() -> dict[str, str]:
            return {"status": "accepted"}

        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            return await client.post(
                "/api/test-mutation",
                headers={
                    "origin": "http://localhost",
                    "x-csrf-token": application.state.csrf_token,
                },
            )

    response = asyncio.run(make_request())

    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}


def test_unrelated_origin_cannot_invoke_api_and_receives_no_cors_access() -> None:
    async def make_requests():
        application = create_app()

        @application.post("/api/test-mutation")
        async def test_mutation() -> dict[str, str]:
            return {"status": "accepted"}

        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            post_response = await client.post(
                "/api/test-mutation",
                headers={
                    "origin": "https://unrelated.example",
                    "x-csrf-token": application.state.csrf_token,
                },
            )
            preflight_response = await client.options(
                "/api/test-mutation",
                headers={
                    "origin": "https://unrelated.example",
                    "access-control-request-method": "POST",
                },
            )
        return post_response, preflight_response

    post_response, preflight_response = asyncio.run(make_requests())

    assert post_response.status_code == 403
    assert post_response.text == "Origin not allowed"
    assert "access-control-allow-origin" not in post_response.headers
    assert preflight_response.status_code == 405
    assert "access-control-allow-origin" not in preflight_response.headers


def test_streaming_path_requires_matching_local_origin() -> None:
    async def make_requests():
        application = create_app()

        @application.get("/api/test-generation/events")
        async def test_events() -> Response:
            return Response("event: done\n\n", media_type="text/event-stream")

        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://localhost"
        ) as client:
            rejected = await client.get(
                "/api/test-generation/events",
                headers={"origin": "https://unrelated.example"},
            )
            accepted = await client.get(
                "/api/test-generation/events",
                headers={"origin": "http://localhost"},
            )
        return rejected, accepted

    rejected, accepted = asyncio.run(make_requests())

    assert rejected.status_code == 403
    assert rejected.text == "Origin not allowed"
    assert accepted.status_code == 200
    assert accepted.headers["content-type"].startswith("text/event-stream")
