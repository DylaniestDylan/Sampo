import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress
from dataclasses import dataclass

from app.harness.tools import (
    HarnessToolBoundary,
    UnexpectedModelToolRequestError,
)
from app.model_runtime.errors import ModelRuntimeError, RuntimeCancelledError
from app.model_runtime.events import (
    ModelEvent,
    ModelFailed,
    ModelStopped,
    ModelToolRequest,
)
from app.model_runtime.request import ModelRequest
from app.model_runtime.runtime import ModelRuntime


def _require_non_blank(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


@dataclass(frozen=True, slots=True, kw_only=True)
class HarnessRequest:
    request_id: str
    user_prompt: str

    def __post_init__(self) -> None:
        _require_non_blank(self.request_id, "request_id")
        _require_non_blank(self.user_prompt, "user_prompt")


PHASE_ONE_APPLICATION_POLICY = "Answer the user's current request."


@dataclass(frozen=True, slots=True, kw_only=True)
class HarnessPolicy:
    application_text: str

    def __post_init__(self) -> None:
        _require_non_blank(self.application_text, "application_text")


MAX_HARNESS_CONTEXT_CHARS = 16_000


def assemble_model_request(
    *,
    request: HarnessRequest,
    policy: HarnessPolicy,
) -> ModelRequest:
    context_size = len(policy.application_text) + len(request.user_prompt)
    if context_size > MAX_HARNESS_CONTEXT_CHARS:
        raise ValueError(
            f"harness context must not exceed {MAX_HARNESS_CONTEXT_CHARS} characters"
        )
    return ModelRequest(
        request_id=request.request_id,
        system_text=policy.application_text,
        user_text=request.user_prompt,
    )


class ApplicationHarness:
    __slots__ = ("_policy", "_runtime", "_tool_boundary")

    def __init__(
        self,
        *,
        runtime: ModelRuntime,
        policy: HarnessPolicy,
        tool_boundary: HarnessToolBoundary,
    ) -> None:
        self._runtime = runtime
        self._policy = policy
        self._tool_boundary = tool_boundary

    async def stream(
        self,
        request: HarnessRequest,
        *,
        cancellation_signal: asyncio.Event | None = None,
    ) -> AsyncIterator[ModelEvent]:
        model_request = assemble_model_request(request=request, policy=self._policy)
        runtime_stream = self._runtime.stream_chat(model_request)
        next_event: asyncio.Task[ModelEvent] | None = None
        cancellation_wait: asyncio.Task[bool] | None = None
        try:
            while True:
                try:
                    if cancellation_signal is None:
                        event = await anext(runtime_stream)
                    else:
                        next_event = asyncio.create_task(anext(runtime_stream))
                        cancellation_wait = asyncio.create_task(
                            cancellation_signal.wait()
                        )
                        await asyncio.wait(
                            {next_event, cancellation_wait},
                            return_when=asyncio.FIRST_COMPLETED,
                        )
                        if cancellation_wait.done() and cancellation_wait.result():
                            await self._runtime.abort(request.request_id)
                            if not next_event.done():
                                next_event.cancel()
                            with suppress(
                                asyncio.CancelledError, StopAsyncIteration
                            ):
                                await next_event
                            yield ModelStopped(request_id=request.request_id)
                            return
                        cancellation_wait.cancel()
                        with suppress(asyncio.CancelledError):
                            await cancellation_wait
                        event = next_event.result()
                        next_event = None
                        cancellation_wait = None
                except StopAsyncIteration:
                    return
                if isinstance(event, ModelToolRequest):
                    try:
                        self._tool_boundary.reject_model_tool_request(event)
                    except UnexpectedModelToolRequestError as error:
                        yield ModelFailed(
                            request_id=request.request_id,
                            message=str(error),
                        )
                        return
                yield event
        except RuntimeCancelledError:
            yield ModelStopped(request_id=request.request_id)
        except ModelRuntimeError as error:
            yield ModelFailed(request_id=request.request_id, message=str(error))
        finally:
            for pending_task in (next_event, cancellation_wait):
                if pending_task is not None and not pending_task.done():
                    pending_task.cancel()
                    with suppress(asyncio.CancelledError, StopAsyncIteration):
                        await pending_task
            await runtime_stream.aclose()
