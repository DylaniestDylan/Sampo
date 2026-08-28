from collections.abc import AsyncIterator

from app.main import create_app
from app.model_runtime import (
    ModelCompleted,
    ModelEvent,
    ModelRequest,
    ModelRuntime,
    RuntimeCapabilities,
)
from tests.runtime_contract import ModelRuntimeContract


class StructurallyCompatibleRuntime:
    async def get_capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(available=True, text_chat=True, streaming=True)

    async def stream_chat(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        yield ModelCompleted(request_id=request.request_id)

    async def abort(self, request_id: str) -> None:
        return None


def test_model_runtime_protocol_defines_structural_boundary() -> None:
    runtime = StructurallyCompatibleRuntime()

    assert isinstance(runtime, ModelRuntime)


def test_runtime_is_injected_at_application_composition_time() -> None:
    runtime = StructurallyCompatibleRuntime()

    application = create_app(model_runtime=runtime)

    assert application.state.model_runtime is runtime
    assert create_app().state.model_runtime is None


def test_reusable_runtime_contract_scaffold_is_available() -> None:
    assert ModelRuntimeContract.__annotations__["expected_text"] is str
    assert ModelRuntimeContract.__abstractmethods__ == frozenset({"create_runtime"})
