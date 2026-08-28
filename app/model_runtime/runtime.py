from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from app.model_runtime.capabilities import RuntimeCapabilities
from app.model_runtime.events import ModelEvent
from app.model_runtime.request import ModelRequest


@runtime_checkable
class ModelRuntime(Protocol):
    async def get_capabilities(self) -> RuntimeCapabilities: ...

    def stream_chat(self, request: ModelRequest) -> AsyncIterator[ModelEvent]: ...

    async def abort(self, request_id: str) -> None: ...
