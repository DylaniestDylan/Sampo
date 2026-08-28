from __future__ import annotations

from asyncio import Queue, QueueEmpty, QueueFull
from dataclasses import dataclass, replace
from enum import StrEnum
from secrets import token_urlsafe


MAX_EPHEMERAL_GENERATIONS = 128
MAX_GENERATION_ERROR_CHARS = 512
MAX_GENERATION_EVENT_TEXT_CHARS = 4_096
GENERATION_EVENT_BUFFER_SIZE = 32


class GenerationStatus(StrEnum):
    STREAMING = "streaming"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"


TERMINAL_GENERATION_STATUSES = frozenset(
    {
        GenerationStatus.COMPLETED,
        GenerationStatus.STOPPED,
        GenerationStatus.FAILED,
    }
)


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerationState:
    generation_id: str
    status: GenerationStatus
    error: str | None = None


class InvalidGenerationTransitionError(RuntimeError):
    pass


class GenerationRegistryCapacityError(RuntimeError):
    pass


class GenerationEventsAlreadyClaimedError(RuntimeError):
    pass


class GenerationEventName(StrEnum):
    STARTED = "generation.started"
    DELTA = "generation.delta"
    COMPLETED = "generation.completed"
    STOPPED = "generation.stopped"
    FAILED = "generation.failed"


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerationEvent:
    name: GenerationEventName
    text: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.text is not None and (
            not self.text or len(self.text) > MAX_GENERATION_EVENT_TEXT_CHARS
        ):
            raise ValueError("generation event text is empty or too large")
        if self.error is not None and (
            not self.error or len(self.error) > MAX_GENERATION_ERROR_CHARS
        ):
            raise ValueError("generation event error is empty or too large")
        if self.name is GenerationEventName.DELTA:
            if self.text is None or self.error is not None:
                raise ValueError("delta event requires only text")
        elif self.name is GenerationEventName.FAILED:
            if self.error is None or self.text is not None:
                raise ValueError("failed event requires only an error")
        elif self.text is not None or self.error is not None:
            raise ValueError("lifecycle event must not contain text or error")


class GenerationEventBuffer:
    """Bounded single-consumer event channel for one ephemeral generation."""

    __slots__ = ("_queue",)

    def __init__(self, *, capacity: int = GENERATION_EVENT_BUFFER_SIZE) -> None:
        if capacity < 1:
            raise ValueError("event buffer capacity must be positive")
        self._queue: Queue[GenerationEvent] = Queue(maxsize=capacity)

    def publish(self, event: GenerationEvent) -> bool:
        try:
            self._queue.put_nowait(event)
        except QueueFull:
            return False
        return True

    def replace_with(self, event: GenerationEvent) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except QueueEmpty:
                break
        self._queue.put_nowait(event)

    async def receive(self) -> GenerationEvent:
        return await self._queue.get()

    @property
    def size(self) -> int:
        return self._queue.qsize()

    @property
    def capacity(self) -> int:
        return self._queue.maxsize


@dataclass(slots=True, kw_only=True)
class _GenerationRecord:
    state: GenerationState
    runtime_request_id: str
    events: GenerationEventBuffer
    events_claimed: bool = False


class GenerationRegistry:
    """Process-local lifecycle ownership; no conversation or durable state."""

    __slots__ = ("_capacity", "_event_buffer_capacity", "_records")

    def __init__(
        self,
        *,
        capacity: int = MAX_EPHEMERAL_GENERATIONS,
        event_buffer_capacity: int = GENERATION_EVENT_BUFFER_SIZE,
    ) -> None:
        if capacity < 1:
            raise ValueError("registry capacity must be positive")
        if event_buffer_capacity < 1:
            raise ValueError("event buffer capacity must be positive")
        self._capacity = capacity
        self._event_buffer_capacity = event_buffer_capacity
        self._records: dict[str, _GenerationRecord] = {}

    def create(self) -> GenerationState:
        self._make_capacity()
        generation_id = self._new_opaque_id()
        runtime_request_id = self._new_opaque_id()
        while runtime_request_id == generation_id:
            runtime_request_id = self._new_opaque_id()
        state = GenerationState(
            generation_id=generation_id,
            status=GenerationStatus.STREAMING,
        )
        self._records[generation_id] = _GenerationRecord(
            state=state,
            runtime_request_id=runtime_request_id,
            events=GenerationEventBuffer(capacity=self._event_buffer_capacity),
        )
        return state

    def get(self, generation_id: str) -> GenerationState | None:
        record = self._records.get(generation_id)
        return record.state if record is not None else None

    def runtime_request_id(self, generation_id: str) -> str | None:
        record = self._records.get(generation_id)
        return record.runtime_request_id if record is not None else None

    def event_buffer(self, generation_id: str) -> GenerationEventBuffer | None:
        record = self._records.get(generation_id)
        return record.events if record is not None else None

    def claim_event_buffer(
        self, generation_id: str
    ) -> GenerationEventBuffer | None:
        record = self._records.get(generation_id)
        if record is None:
            return None
        if record.events_claimed:
            raise GenerationEventsAlreadyClaimedError(
                "generation event stream is already claimed"
            )
        record.events_claimed = True
        return record.events

    def transition(
        self,
        generation_id: str,
        status: GenerationStatus,
        *,
        error: str | None = None,
    ) -> GenerationState | None:
        record = self._records.get(generation_id)
        if record is None:
            return None
        current = record.state
        if current.status in TERMINAL_GENERATION_STATUSES:
            raise InvalidGenerationTransitionError(
                f"generation is already terminal: {current.status}"
            )
        if status not in TERMINAL_GENERATION_STATUSES:
            raise InvalidGenerationTransitionError(
                f"generation cannot transition to {status}"
            )
        bounded_error = (
            self._bounded_error(error)
            if status is GenerationStatus.FAILED
            else None
        )
        if status is GenerationStatus.FAILED and bounded_error is None:
            raise ValueError("failed generation requires an error")
        if status is not GenerationStatus.FAILED and error is not None:
            raise ValueError("only failed generations may contain an error")
        record.state = replace(current, status=status, error=bounded_error)
        return record.state

    def _make_capacity(self) -> None:
        if len(self._records) < self._capacity:
            return
        terminal_id = next(
            (
                generation_id
                for generation_id, record in self._records.items()
                if record.state.status in TERMINAL_GENERATION_STATUSES
            ),
            None,
        )
        if terminal_id is None:
            raise GenerationRegistryCapacityError(
                "too many active ephemeral generations"
            )
        del self._records[terminal_id]

    @staticmethod
    def _new_opaque_id() -> str:
        return token_urlsafe(24)

    @staticmethod
    def _bounded_error(error: str | None) -> str | None:
        if error is None:
            return None
        normalized = error.strip()
        if not normalized:
            raise ValueError("generation error must not be blank")
        return normalized[:MAX_GENERATION_ERROR_CHARS]
