from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class RuntimeCapabilities:
    available: bool
    text_chat: bool
    streaming: bool
