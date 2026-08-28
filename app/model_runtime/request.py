from dataclasses import dataclass


MAX_OUTPUT_TOKENS = 8_192


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelRequest:
    request_id: str
    system_text: str
    user_text: str
    model: str | None = None
    max_output_tokens: int = 512

    def __post_init__(self) -> None:
        for field_name in ("request_id", "system_text", "user_text"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be blank")

        if self.model is not None and not self.model.strip():
            raise ValueError("model must not be blank when provided")
        if not 1 <= self.max_output_tokens <= MAX_OUTPUT_TOKENS:
            raise ValueError(
                f"max_output_tokens must be between 1 and {MAX_OUTPUT_TOKENS}"
            )
