from enum import StrEnum


class RuntimeErrorCode(StrEnum):
    UNAVAILABLE = "unavailable"
    INVALID_CONFIGURATION = "invalid_configuration"
    INCOMPATIBLE_CAPABILITY = "incompatible_capability"
    CANCELLED = "cancelled"
    RUNTIME_FAILURE = "runtime_failure"


class ModelRuntimeError(Exception):
    code: RuntimeErrorCode

    def __init__(self, message: str) -> None:
        if not message.strip():
            raise ValueError("runtime error message must not be blank")
        super().__init__(message)


class RuntimeUnavailableError(ModelRuntimeError):
    code = RuntimeErrorCode.UNAVAILABLE


class RuntimeConfigurationError(ModelRuntimeError):
    code = RuntimeErrorCode.INVALID_CONFIGURATION


class RuntimeCapabilityError(ModelRuntimeError):
    code = RuntimeErrorCode.INCOMPATIBLE_CAPABILITY


class RuntimeCancelledError(ModelRuntimeError):
    code = RuntimeErrorCode.CANCELLED


class RuntimeFailureError(ModelRuntimeError):
    code = RuntimeErrorCode.RUNTIME_FAILURE
