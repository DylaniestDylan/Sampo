from dataclasses import dataclass
from typing import Never

from app.model_runtime.events import ModelToolRequest


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelToolDescription:
    name: str


class ToolRegistry:
    __slots__ = ()

    _MODEL_TOOL_DESCRIPTIONS: tuple[ModelToolDescription, ...] = ()

    def model_tool_descriptions(self) -> tuple[ModelToolDescription, ...]:
        return self._MODEL_TOOL_DESCRIPTIONS


class UnexpectedModelToolRequestError(Exception):
    code = "unsupported_model_tool_request"

    def __init__(self) -> None:
        super().__init__("model tool requests are unsupported")


class HarnessToolBoundary:
    def __init__(self, *, registry: ToolRegistry) -> None:
        self._registry = registry

    def model_tool_descriptions(self) -> tuple[ModelToolDescription, ...]:
        return self._registry.model_tool_descriptions()

    def reject_model_tool_request(self, request: ModelToolRequest) -> Never:
        raise UnexpectedModelToolRequestError
