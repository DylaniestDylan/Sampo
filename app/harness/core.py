from collections.abc import AsyncIterator
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

    async def stream(self, request: HarnessRequest) -> AsyncIterator[ModelEvent]:
        model_request = assemble_model_request(request=request, policy=self._policy)
        try:
            async for event in self._runtime.stream_chat(model_request):
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
