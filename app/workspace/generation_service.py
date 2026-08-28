from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from app.harness import ApplicationHarness, HarnessRequest
from app.model_runtime import (
    ModelCompleted,
    ModelDelta,
    ModelFailed,
    ModelStarted,
    ModelStopped,
)
from app.workspace.generations import (
    MAX_GENERATION_ERROR_CHARS,
    MAX_GENERATION_EVENT_TEXT_CHARS,
    TERMINAL_GENERATION_STATUSES,
    GenerationEvent,
    GenerationEventName,
    GenerationRegistry,
    GenerationState,
    GenerationStatus,
    InvalidGenerationTransitionError,
)


SLOW_CONSUMER_ERROR = "generation event consumer could not keep up"
INTERNAL_GENERATION_ERROR = "generation failed inside the application"


class UnknownGenerationError(LookupError):
    pass


class GenerationService:
    """Backend-owned composition of ephemeral lifecycle and harness execution."""

    __slots__ = ("_cancellation_signals", "_harness", "_registry", "_tasks")

    def __init__(
        self,
        *,
        harness: ApplicationHarness,
        registry: GenerationRegistry | None = None,
    ) -> None:
        self._harness = harness
        self._registry = registry or GenerationRegistry()
        self._cancellation_signals: dict[str, asyncio.Event] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def create_generation(self, prompt: str) -> GenerationState:
        if not prompt.strip():
            raise ValueError("prompt must not be blank")
        state = self._registry.create()
        runtime_request_id = self._registry.runtime_request_id(state.generation_id)
        if runtime_request_id is None:
            raise RuntimeError("generation runtime request ID is unavailable")
        cancellation_signal = asyncio.Event()
        self._cancellation_signals[state.generation_id] = cancellation_signal
        task = asyncio.create_task(
            self._run_generation(
                generation_id=state.generation_id,
                runtime_request_id=runtime_request_id,
                prompt=prompt,
                cancellation_signal=cancellation_signal,
            )
        )
        self._tasks[state.generation_id] = task
        task.add_done_callback(
            lambda completed, generation_id=state.generation_id: self._forget_task(
                generation_id, completed
            )
        )
        return state

    def get_generation(self, generation_id: str) -> GenerationState | None:
        return self._registry.get(generation_id)

    async def cancel_generation(
        self, generation_id: str
    ) -> GenerationState | None:
        state = self._registry.get(generation_id)
        if state is None or state.status in TERMINAL_GENERATION_STATUSES:
            return state
        cancellation_signal = self._cancellation_signals.get(generation_id)
        task = self._tasks.get(generation_id)
        if cancellation_signal is None or task is None:
            raise RuntimeError("active generation cancellation state is unavailable")
        cancellation_signal.set()
        await task
        return self._registry.get(generation_id)

    def stream_events(self, generation_id: str) -> AsyncIterator[GenerationEvent]:
        event_buffer = self._registry.claim_event_buffer(generation_id)
        if event_buffer is None:
            raise UnknownGenerationError(generation_id)

        async def consume() -> AsyncIterator[GenerationEvent]:
            try:
                while True:
                    event = await event_buffer.receive()
                    yield event
                    if event.name in {
                        GenerationEventName.COMPLETED,
                        GenerationEventName.STOPPED,
                        GenerationEventName.FAILED,
                    }:
                        return
            finally:
                state = self._registry.get(generation_id)
                if (
                    state is not None
                    and state.status not in TERMINAL_GENERATION_STATUSES
                ):
                    await self._stop_disconnected_generation(generation_id)

        return consume()

    async def _run_generation(
        self,
        *,
        generation_id: str,
        runtime_request_id: str,
        prompt: str,
        cancellation_signal: asyncio.Event,
    ) -> None:
        try:
            self._registry.transition(
                generation_id,
                GenerationStatus.STREAMING,
            )
            async for model_event in self._harness.stream(
                HarnessRequest(
                    request_id=runtime_request_id,
                    user_prompt=prompt,
                ),
                cancellation_signal=cancellation_signal,
            ):
                if cancellation_signal.is_set() and not isinstance(
                    model_event, (ModelStopped, ModelFailed)
                ):
                    continue
                if isinstance(model_event, ModelStarted):
                    if not self._publish(
                        generation_id,
                        GenerationEvent(name=GenerationEventName.STARTED),
                    ):
                        return
                elif isinstance(model_event, ModelDelta):
                    for text in self._bounded_text_parts(model_event.text):
                        if not self._publish(
                            generation_id,
                            GenerationEvent(
                                name=GenerationEventName.DELTA,
                                text=text,
                            ),
                        ):
                            return
                elif isinstance(model_event, ModelCompleted):
                    self._finish(
                        generation_id,
                        status=GenerationStatus.COMPLETED,
                        event=GenerationEvent(name=GenerationEventName.COMPLETED),
                    )
                    return
                elif isinstance(model_event, ModelStopped):
                    self._finish(
                        generation_id,
                        status=GenerationStatus.STOPPED,
                        event=GenerationEvent(name=GenerationEventName.STOPPED),
                    )
                    return
                elif isinstance(model_event, ModelFailed):
                    error = model_event.message[:MAX_GENERATION_ERROR_CHARS]
                    self._finish(
                        generation_id,
                        status=GenerationStatus.FAILED,
                        event=GenerationEvent(
                            name=GenerationEventName.FAILED,
                            error=error,
                        ),
                        error=error,
                    )
                    return
            if cancellation_signal.is_set():
                self._finish_if_active(
                    generation_id,
                    status=GenerationStatus.STOPPED,
                    event=GenerationEvent(name=GenerationEventName.STOPPED),
                )
            else:
                self._fail(generation_id, INTERNAL_GENERATION_ERROR)
        except asyncio.CancelledError:
            self._finish_if_active(
                generation_id,
                status=GenerationStatus.STOPPED,
                event=GenerationEvent(name=GenerationEventName.STOPPED),
            )
        except Exception:
            self._fail(generation_id, INTERNAL_GENERATION_ERROR)

    def _publish(self, generation_id: str, event: GenerationEvent) -> bool:
        event_buffer = self._registry.event_buffer(generation_id)
        if event_buffer is None:
            return False
        if event_buffer.publish(event):
            return True
        self._fail(generation_id, SLOW_CONSUMER_ERROR, replace_backlog=True)
        return False

    def _finish(
        self,
        generation_id: str,
        *,
        status: GenerationStatus,
        event: GenerationEvent,
        error: str | None = None,
    ) -> None:
        event_buffer = self._registry.event_buffer(generation_id)
        if event_buffer is None:
            return
        if not event_buffer.publish(event):
            if status is GenerationStatus.STOPPED:
                event_buffer.replace_with(event)
            else:
                self._fail(
                    generation_id,
                    SLOW_CONSUMER_ERROR,
                    replace_backlog=True,
                )
                return
        self._registry.transition(generation_id, status, error=error)

    def _finish_if_active(
        self,
        generation_id: str,
        *,
        status: GenerationStatus,
        event: GenerationEvent,
    ) -> None:
        state = self._registry.get(generation_id)
        if state is None or state.status in TERMINAL_GENERATION_STATUSES:
            return
        try:
            self._finish(generation_id, status=status, event=event)
        except InvalidGenerationTransitionError:
            return

    def _fail(
        self,
        generation_id: str,
        error: str,
        *,
        replace_backlog: bool = False,
    ) -> None:
        state = self._registry.get(generation_id)
        if state is None or state.status in TERMINAL_GENERATION_STATUSES:
            return
        bounded_error = error[:MAX_GENERATION_ERROR_CHARS]
        self._registry.transition(
            generation_id,
            GenerationStatus.FAILED,
            error=bounded_error,
        )
        event_buffer = self._registry.event_buffer(generation_id)
        if event_buffer is None:
            return
        event = GenerationEvent(
            name=GenerationEventName.FAILED,
            error=bounded_error,
        )
        if replace_backlog or not event_buffer.publish(event):
            event_buffer.replace_with(event)

    async def _stop_disconnected_generation(self, generation_id: str) -> None:
        await self.cancel_generation(generation_id)

    def _forget_task(
        self, generation_id: str, completed_task: asyncio.Task[None]
    ) -> None:
        if self._tasks.get(generation_id) is completed_task:
            self._tasks.pop(generation_id, None)
            self._cancellation_signals.pop(generation_id, None)

    @staticmethod
    def _bounded_text_parts(text: str) -> tuple[str, ...]:
        return tuple(
            text[index : index + MAX_GENERATION_EVENT_TEXT_CHARS]
            for index in range(0, len(text), MAX_GENERATION_EVENT_TEXT_CHARS)
        )
