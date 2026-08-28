from dataclasses import dataclass


def _require_non_blank(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelStarted:
    request_id: str

    def __post_init__(self) -> None:
        _require_non_blank(self.request_id, "request_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelDelta:
    request_id: str
    text: str

    def __post_init__(self) -> None:
        _require_non_blank(self.request_id, "request_id")
        if not self.text:
            raise ValueError("text must not be empty")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelToolRequest:
    request_id: str

    def __post_init__(self) -> None:
        _require_non_blank(self.request_id, "request_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelCompleted:
    request_id: str

    def __post_init__(self) -> None:
        _require_non_blank(self.request_id, "request_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelStopped:
    request_id: str

    def __post_init__(self) -> None:
        _require_non_blank(self.request_id, "request_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelFailed:
    request_id: str
    message: str

    def __post_init__(self) -> None:
        _require_non_blank(self.request_id, "request_id")
        _require_non_blank(self.message, "message")


type ModelEvent = (
    ModelStarted
    | ModelDelta
    | ModelToolRequest
    | ModelCompleted
    | ModelStopped
    | ModelFailed
)
