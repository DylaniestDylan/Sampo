from asyncio import Event
from collections.abc import AsyncIterator, Iterable

from app.model_runtime.capabilities import RuntimeCapabilities
from app.model_runtime.events import (
    ModelCompleted,
    ModelDelta,
    ModelEvent,
    ModelStarted,
    ModelToolRequest,
)
from app.model_runtime.errors import ModelRuntimeError
from app.model_runtime.request import ModelRequest


class FakeModelRuntime:
    def __init__(
        self,
        *,
        chunks: Iterable[str] = ("Fake response",),
        chunk_gate: Event | None = None,
        failure: ModelRuntimeError | None = None,
        failure_after_chunks: int = 0,
        tool_request_after_chunks: int | None = None,
    ) -> None:
        self._chunks = tuple(chunks)
        self._chunk_gate = chunk_gate
        self._failure = failure
        self._failure_after_chunks = failure_after_chunks
        self._tool_request_after_chunks = tool_request_after_chunks
        self._abort_calls: list[str] = []
        self._stream_requests: list[ModelRequest] = []
        if not self._chunks or any(not chunk for chunk in self._chunks):
            raise ValueError("chunks must contain at least one non-empty text chunk")
        if not 0 <= failure_after_chunks <= len(self._chunks):
            raise ValueError("failure_after_chunks must be within the configured chunks")
        if tool_request_after_chunks is not None and not (
            0 <= tool_request_after_chunks <= len(self._chunks)
        ):
            raise ValueError(
                "tool_request_after_chunks must be within the configured chunks"
            )

    async def get_capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(available=True, text_chat=True, streaming=True)

    async def stream_chat(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        self._stream_requests.append(request)
        yield ModelStarted(request_id=request.request_id)
        if self._tool_request_after_chunks == 0:
            yield ModelToolRequest(request_id=request.request_id)
            return
        for chunk_index, chunk in enumerate(self._chunks):
            if self._failure is not None and chunk_index == self._failure_after_chunks:
                raise self._failure
            if self._chunk_gate is not None:
                await self._chunk_gate.wait()
            yield ModelDelta(request_id=request.request_id, text=chunk)
            if self._tool_request_after_chunks == chunk_index + 1:
                yield ModelToolRequest(request_id=request.request_id)
                return
        if (
            self._failure is not None
            and self._failure_after_chunks == len(self._chunks)
        ):
            raise self._failure
        yield ModelCompleted(request_id=request.request_id)

    async def abort(self, request_id: str) -> None:
        if not request_id.strip():
            raise ValueError("request_id must not be blank")
        self._abort_calls.append(request_id)

    @property
    def abort_calls(self) -> tuple[str, ...]:
        return tuple(self._abort_calls)

    @property
    def stream_requests(self) -> tuple[ModelRequest, ...]:
        return tuple(self._stream_requests)
