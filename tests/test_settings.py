import pytest

from app.settings import ApplicationSettings


def test_application_settings_hold_bind_configuration() -> None:
    settings = ApplicationSettings(
        bind_host="127.0.0.1",
        bind_port=8000,
        runtime_endpoint="http://127.0.0.1:8081",
        runtime_model="phase-one-model",
    )

    assert settings.bind_host == "127.0.0.1"
    assert settings.bind_port == 8000
    assert settings.runtime_endpoint == "http://127.0.0.1:8081"
    assert settings.runtime_model == "phase-one-model"


def test_application_settings_default_bind_host_to_loopback() -> None:
    settings = ApplicationSettings(bind_port=8000)

    assert settings.bind_host == "127.0.0.1"
    assert settings.runtime_endpoint == "http://127.0.0.1:8080"
    assert settings.runtime_model == "local-model"


@pytest.mark.parametrize("field_name", ["runtime_endpoint", "runtime_model"])
def test_application_settings_rejects_blank_runtime_configuration(
    field_name: str,
) -> None:
    values = {"bind_port": 8000, field_name: "  "}

    with pytest.raises(ValueError, match=field_name):
        ApplicationSettings(**values)


@pytest.mark.parametrize(
    "runtime_endpoint",
    [
        "https://127.0.0.1:8080",
        "http://localhost:8080",
        "http://0.0.0.0:8080",
        "http://192.168.1.10:8080",
        "http://203.0.113.10:8080",
        "http://models.example.com/v1",
        "http://127.0.0.1",
        "http://user:password@127.0.0.1:8080",
    ],
)
def test_application_settings_rejects_non_loopback_runtime_endpoint(
    runtime_endpoint: str,
) -> None:
    with pytest.raises(ValueError, match="numeric loopback IP"):
        ApplicationSettings(bind_port=8000, runtime_endpoint=runtime_endpoint)


@pytest.mark.parametrize(
    "runtime_endpoint",
    ["http://127.0.0.1:8080", "http://[::1]:8080"],
)
def test_application_settings_accepts_numeric_loopback_runtime_endpoint(
    runtime_endpoint: str,
) -> None:
    settings = ApplicationSettings(
        bind_port=8000,
        runtime_endpoint=runtime_endpoint,
    )

    assert settings.runtime_endpoint == runtime_endpoint


@pytest.mark.parametrize(
    "bind_host",
    ["0.0.0.0", "::", "192.168.1.10", "203.0.113.10", "localhost"],
)
def test_application_settings_rejects_unsupported_bind_host(bind_host: str) -> None:
    with pytest.raises(ValueError, match="numeric loopback IP address"):
        ApplicationSettings(bind_host=bind_host, bind_port=8000)
