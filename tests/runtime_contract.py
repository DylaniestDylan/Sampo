import asyncio
from abc import ABC, abstractmethod

from app.model_runtime import (
    ModelCompleted,
    ModelDelta,
    ModelEvent,
    ModelFailed,
    ModelRequest,
    ModelRuntime,
    ModelStarted,
    ModelStopped,
    RuntimeCapabilities,
)


class ModelRuntimeContract(ABC):
    expected_text: str

    @abstractmethod
    def create_runtime(self) -> ModelRuntime:
        raise NotImplementedError

    def create_request(self) -> ModelRequest:
        return ModelRequest(
            request_id="contract-request",
            system_text="Application policy",
            user_text="Contract prompt",
        )

    def test_runtime_contract_reports_capabilities(self) -> None:
        capabilities = asyncio.run(self.create_runtime().get_capabilities())

        assert isinstance(capabilities, RuntimeCapabilities)

    def test_runtime_contract_streams_application_events(self) -> None:
        async def collect_events() -> list[ModelEvent]:
            runtime = self.create_runtime()
            return [event async for event in runtime.stream_chat(self.create_request())]

        events = asyncio.run(collect_events())

        assert isinstance(events[0], ModelStarted)
        assert isinstance(events[-1], ModelCompleted)
        assert all(
            isinstance(
                event,
                ModelStarted
                | ModelDelta
                | ModelCompleted
                | ModelStopped
                | ModelFailed,
            )
            for event in events
        )
        assert {event.request_id for event in events} == {"contract-request"}
        assert "".join(
            event.text for event in events if isinstance(event, ModelDelta)
        ) == self.expected_text

    def test_runtime_contract_accepts_abort(self) -> None:
        runtime = self.create_runtime()

        asyncio.run(runtime.abort("contract-request"))
