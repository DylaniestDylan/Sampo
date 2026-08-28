from secrets import compare_digest
from urllib.parse import urlsplit

from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send


TRUSTED_LOCAL_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
DEFAULT_PORTS = {"http": 80, "https": 443}


def is_trusted_local_host(host_header: str | None) -> bool:
    if not host_header:
        return False

    try:
        parsed = urlsplit(f"//{host_header}")
        hostname = parsed.hostname
        parsed.port
    except ValueError:
        return False

    return (
        hostname is not None
        and hostname.lower() in TRUSTED_LOCAL_HOSTS
        and parsed.username is None
        and parsed.password is None
        and not parsed.path
        and not parsed.query
        and not parsed.fragment
    )


def is_same_origin(
    origin_header: str | None, *, request_scheme: str, request_host: str
) -> bool:
    if not origin_header or request_scheme not in DEFAULT_PORTS:
        return False

    try:
        origin = urlsplit(origin_header)
        request = urlsplit(f"{request_scheme}://{request_host}")
        origin_port = origin.port or DEFAULT_PORTS.get(origin.scheme)
        request_port = request.port or DEFAULT_PORTS[request_scheme]
    except ValueError:
        return False

    return (
        origin.scheme == request_scheme
        and origin.scheme in DEFAULT_PORTS
        and origin.hostname is not None
        and request.hostname is not None
        and origin.hostname.lower() == request.hostname.lower()
        and origin_port == request_port
        and origin.username is None
        and origin.password is None
        and origin.path == ""
        and not origin.query
        and not origin.fragment
    )


class TrustedLocalHostMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in {"http", "websocket"}:
            host_header = Headers(scope=scope).get("host")
            if not is_trusted_local_host(host_header):
                response = PlainTextResponse("Invalid host header", status_code=400)
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)


class BrowserMutationProtectionMiddleware:
    _STATE_CHANGING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

    def __init__(self, app: ASGIApp, *, csrf_token: str) -> None:
        self.app = app
        self.csrf_token = csrf_token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        mutation_request = self._is_mutation_request(scope)
        streaming_request = self._is_streaming_request(scope)
        if mutation_request or streaming_request:
            headers = Headers(scope=scope)
            if not is_same_origin(
                headers.get("origin"),
                request_scheme=scope["scheme"],
                request_host=headers.get("host", ""),
            ):
                response = PlainTextResponse("Origin not allowed", status_code=403)
                await response(scope, receive, send)
                return

            if mutation_request:
                submitted_token = headers.get("x-csrf-token", "")
                if not compare_digest(submitted_token, self.csrf_token):
                    response = PlainTextResponse("Invalid CSRF token", status_code=403)
                    await response(scope, receive, send)
                    return

        await self.app(scope, receive, send)

    @classmethod
    def _is_mutation_request(cls, scope: Scope) -> bool:
        if scope["type"] != "http":
            return False
        path = scope["path"]
        return scope["method"] in cls._STATE_CHANGING_METHODS and (
            path == "/api" or path.startswith("/api/")
        )

    @staticmethod
    def _is_streaming_request(scope: Scope) -> bool:
        if scope["type"] != "http" or scope["method"] != "GET":
            return False
        path = scope["path"]
        return path.startswith("/api/") and path.endswith("/events")
