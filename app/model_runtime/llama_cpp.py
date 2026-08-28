import json
from collections.abc import AsyncIterator
from typing import Protocol

import httpx

from app.model_runtime.capabilities import RuntimeCapabilities
from app.model_runtime.endpoint import validate_local_runtime_endpoint
from app.model_runtime.errors import (
    RuntimeCancelledError,
    RuntimeConfigurationError,
    RuntimeFailureError,
    RuntimeUnavailableError,
)
from app.model_runtime.events import (
    ModelCompleted,
    ModelDelta,
    ModelEvent,
    ModelStarted,
    ModelToolRequest,
)
from app.model_runtime.request import ModelRequest


def _request_payload(request: ModelRequest, *, configured_model: str) -> dict[str, object]:
    return {
        "model": request.model or configured_model,
        "messages": [
            {"role": "system", "content": request.system_text},
            {"role": "user", "content": request.user_text},
        ],
        "max_tokens": request.max_output_tokens,
        "stream": True,
    }


class _LlamaCppTransport(Protocol):
    async def probe_health(self) -> object: ...

    def stream_lines(
        self,
        *,
        request_id: str,
        payload: dict[str, object],
    ) -> AsyncIterator[str]: ...

    async def abort(self, request_id: str) -> None: ...


class _TransportConnectionError(Exception):
    pass


class _TransportHttpError(Exception):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"transport HTTP status {status_code}")


class _TransportProtocolError(Exception):
    pass


class _HttpxLlamaCppTransport:
    def __init__(self, *, endpoint: str, timeout_seconds: float) -> None:
        self._endpoint = endpoint
        self._timeout = httpx.Timeout(timeout_seconds)
        self._active_responses: dict[str, httpx.Response] = {}

    async def probe_health(self) -> object:
        try:
            async with httpx.AsyncClient(
                base_url=self._endpoint,
                timeout=self._timeout,
                trust_env=False,
            ) as client:
                response = await client.get("/health")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as error:
            raise _TransportHttpError(error.response.status_code) from error
        except httpx.RequestError as error:
            raise _TransportConnectionError from error
        except ValueError as error:
            raise _TransportProtocolError from error

    async def stream_lines(
        self,
        *,
        request_id: str,
        payload: dict[str, object],
    ) -> AsyncIterator[str]:
        try:
            async with httpx.AsyncClient(
                base_url=self._endpoint,
                timeout=self._timeout,
                trust_env=False,
            ) as client:
                async with client.stream(
                    "POST",
                    "/v1/chat/completions",
                    json=payload,
                ) as response:
                    self._active_responses[request_id] = response
                    try:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            yield line
                    finally:
                        self._active_responses.pop(request_id, None)
        except httpx.HTTPStatusError as error:
            raise _TransportHttpError(error.response.status_code) from error
        except httpx.RequestError as error:
            raise _TransportConnectionError from error

    async def abort(self, request_id: str) -> None:
        response = self._active_responses.get(request_id)
        if response is not None:
            try:
                await response.aclose()
            except httpx.RequestError as error:
                raise _TransportConnectionError from error


class LlamaCppModelRuntime:
    def __init__(
        self,
        *,
        endpoint: str,
        model: str,
        timeout_seconds: float = 30.0,
        transport: _LlamaCppTransport | None = None,
    ) -> None:
        try:
            self._endpoint = validate_local_runtime_endpoint(endpoint)
        except ValueError as error:
            raise RuntimeConfigurationError(str(error)) from error
        if not model.strip():
            raise RuntimeConfigurationError("runtime model must not be blank")
        if timeout_seconds <= 0:
            raise RuntimeConfigurationError("runtime timeout must be positive")
        self._model = model
        self._transport = transport or _HttpxLlamaCppTransport(
            endpoint=self._endpoint,
            timeout_seconds=timeout_seconds,
        )
        self._active_request_ids: set[str] = set()
        self._cancelled_request_ids: set[str] = set()

    def _translate_request(self, request: ModelRequest) -> dict[str, object]:
        return _request_payload(request, configured_model=self._model)

    async def get_capabilities(self) -> RuntimeCapabilities:
        try:
            health = await self._transport.probe_health()
        except (_TransportConnectionError, _TransportHttpError) as error:
            raise RuntimeUnavailableError(
                "local llama.cpp runtime is unavailable"
            ) from error
        except _TransportProtocolError as error:
            raise RuntimeFailureError(
                "local llama.cpp runtime returned an invalid health response"
            ) from error
        if not isinstance(health, dict) or health.get("status") != "ok":
            raise RuntimeUnavailableError(
                "local llama.cpp runtime returned an invalid health response"
            )
        return RuntimeCapabilities(available=True, text_chat=True, streaming=True)

    async def stream_chat(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        request_id = request.request_id
        if request_id in self._active_request_ids:
            raise RuntimeFailureError("runtime request ID is already active")
        self._active_request_ids.add(request_id)
        try:
            yield ModelStarted(request_id=request_id)
            saw_done = False
            try:
                async for line in self._transport.stream_lines(
                    request_id=request_id,
                    payload=self._translate_request(request),
                ):
                    if request_id in self._cancelled_request_ids:
                        raise RuntimeCancelledError("llama.cpp request was cancelled")
                    if not line:
                        continue
                    if not line.startswith("data:"):
                        raise RuntimeFailureError("llama.cpp returned a malformed stream")
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        saw_done = True
                        break
                    try:
                        chunk = json.loads(data)
                        if not isinstance(chunk, dict):
                            raise TypeError
                        choices = chunk.get("choices")
                        if (
                            not isinstance(choices, list)
                            or not choices
                            or not isinstance(choices[0], dict)
                        ):
                            raise TypeError
                        delta = choices[0].get("delta")
                        if not isinstance(delta, dict):
                            raise TypeError
                        tool_calls = delta.get("tool_calls")
                        if tool_calls is not None and (
                            not isinstance(tool_calls, list)
                            or not all(
                                isinstance(tool_call, dict)
                                for tool_call in tool_calls
                            )
                        ):
                            raise TypeError
                        content = delta.get("content")
                    except (
                        json.JSONDecodeError,
                        KeyError,
                        IndexError,
                        TypeError,
                    ) as error:
                        raise RuntimeFailureError(
                            "llama.cpp returned a malformed stream"
                        ) from error
                    if tool_calls:
                        yield ModelToolRequest(request_id=request_id)
                        return
                    if content is not None:
                        if not isinstance(content, str) or not content:
                            raise RuntimeFailureError(
                                "llama.cpp returned a malformed stream"
                            )
                        yield ModelDelta(request_id=request_id, text=content)
            except _TransportConnectionError as error:
                if request_id in self._cancelled_request_ids:
                    raise RuntimeCancelledError(
                        "llama.cpp request was cancelled"
                    ) from error
                raise RuntimeFailureError(
                    "local llama.cpp stream connection failed"
                ) from error
            except _TransportHttpError as error:
                raise RuntimeFailureError(
                    f"local llama.cpp request failed with HTTP {error.status_code}"
                ) from error
            except _TransportProtocolError as error:
                raise RuntimeFailureError(
                    "llama.cpp returned a malformed stream"
                ) from error
            if request_id in self._cancelled_request_ids:
                raise RuntimeCancelledError("llama.cpp request was cancelled")
            if not saw_done:
                raise RuntimeFailureError("llama.cpp stream ended before completion")
            yield ModelCompleted(request_id=request_id)
        finally:
            self._active_request_ids.discard(request_id)
            self._cancelled_request_ids.discard(request_id)

    async def abort(self, request_id: str) -> None:
        if not request_id.strip():
            raise ValueError("request_id must not be blank")
        if request_id in self._active_request_ids:
            self._cancelled_request_ids.add(request_id)
        try:
            await self._transport.abort(request_id)
        except (_TransportConnectionError, _TransportHttpError) as error:
            raise RuntimeFailureError("local llama.cpp cancellation failed") from error
