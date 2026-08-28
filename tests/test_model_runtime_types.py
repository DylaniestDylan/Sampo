from dataclasses import FrozenInstanceError, fields

import pytest

from app.model_runtime import (
    ModelCompleted,
    ModelDelta,
    ModelFailed,
    ModelRequest,
    ModelRuntimeError,
    ModelStarted,
    ModelStopped,
    RuntimeCancelledError,
    RuntimeCapabilityError,
    RuntimeCapabilities,
    RuntimeConfigurationError,
    RuntimeErrorCode,
    RuntimeFailureError,
    RuntimeUnavailableError,
)


def test_runtime_capabilities_describe_phase_one_runtime_facts() -> None:
    capabilities = RuntimeCapabilities(
        available=True,
        text_chat=True,
        streaming=True,
    )

    assert capabilities.available is True
    assert capabilities.text_chat is True
    assert capabilities.streaming is True


def test_model_request_contains_only_phase_one_runtime_inputs() -> None:
    request = ModelRequest(
        request_id="request-1",
        system_text="Answer the current request.",
        user_text="Explain this function.",
        model="local-model",
        max_output_tokens=256,
    )

    assert {field.name for field in fields(request)} == {
        "request_id",
        "system_text",
        "user_text",
        "model",
        "max_output_tokens",
    }


@pytest.mark.parametrize("field_name", ["request_id", "system_text", "user_text"])
def test_model_request_rejects_blank_required_text(field_name: str) -> None:
    values = {
        "request_id": "request-1",
        "system_text": "Application policy",
        "user_text": "User prompt",
    }
    values[field_name] = "  "

    with pytest.raises(ValueError, match=field_name):
        ModelRequest(**values)


def test_application_owned_model_event_vocabulary() -> None:
    events = (
        ModelStarted(request_id="request-1"),
        ModelDelta(request_id="request-1", text="Hello"),
        ModelCompleted(request_id="request-1"),
        ModelStopped(request_id="request-2"),
        ModelFailed(request_id="request-3", message="runtime failed"),
    )

    assert tuple(type(event).__name__ for event in events) == (
        "ModelStarted",
        "ModelDelta",
        "ModelCompleted",
        "ModelStopped",
        "ModelFailed",
    )


def test_model_delta_rejects_empty_text() -> None:
    with pytest.raises(ValueError, match="text must not be empty"):
        ModelDelta(request_id="request-1", text="")


@pytest.mark.parametrize(
    ("error_type", "expected_code"),
    [
        (RuntimeUnavailableError, RuntimeErrorCode.UNAVAILABLE),
        (RuntimeConfigurationError, RuntimeErrorCode.INVALID_CONFIGURATION),
        (RuntimeCapabilityError, RuntimeErrorCode.INCOMPATIBLE_CAPABILITY),
        (RuntimeCancelledError, RuntimeErrorCode.CANCELLED),
        (RuntimeFailureError, RuntimeErrorCode.RUNTIME_FAILURE),
    ],
)
def test_runtime_error_taxonomy(error_type, expected_code: RuntimeErrorCode) -> None:
    error = error_type("known runtime problem")

    assert isinstance(error, ModelRuntimeError)
    assert error.code is expected_code
    assert str(error) == "known runtime problem"


@pytest.mark.parametrize("max_output_tokens", [0, 8_193])
def test_model_request_rejects_unbounded_output_limit(
    max_output_tokens: int,
) -> None:
    with pytest.raises(ValueError, match="max_output_tokens"):
        ModelRequest(
            request_id="request-1",
            system_text="Application policy",
            user_text="User prompt",
            max_output_tokens=max_output_tokens,
        )


def test_model_request_rejects_blank_optional_model() -> None:
    with pytest.raises(ValueError, match="model"):
        ModelRequest(
            request_id="request-1",
            system_text="Application policy",
            user_text="User prompt",
            model=" ",
        )


def test_runtime_values_are_immutable() -> None:
    capabilities = RuntimeCapabilities(
        available=True,
        text_chat=True,
        streaming=True,
    )

    with pytest.raises(FrozenInstanceError):
        setattr(capabilities, "available", False)


def test_failed_event_and_runtime_error_reject_blank_messages() -> None:
    with pytest.raises(ValueError, match="message"):
        ModelFailed(request_id="request-1", message=" ")
    with pytest.raises(ValueError, match="runtime error message"):
        RuntimeFailureError(" ")
