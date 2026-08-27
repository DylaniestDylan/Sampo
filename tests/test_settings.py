import pytest

from app.settings import ApplicationSettings


def test_application_settings_hold_bind_configuration() -> None:
    settings = ApplicationSettings(bind_host="127.0.0.1", bind_port=8000)

    assert settings.bind_host == "127.0.0.1"
    assert settings.bind_port == 8000


def test_application_settings_default_bind_host_to_loopback() -> None:
    settings = ApplicationSettings(bind_port=8000)

    assert settings.bind_host == "127.0.0.1"


@pytest.mark.parametrize(
    "bind_host",
    ["0.0.0.0", "::", "192.168.1.10", "203.0.113.10", "localhost"],
)
def test_application_settings_rejects_unsupported_bind_host(bind_host: str) -> None:
    with pytest.raises(ValueError, match="numeric loopback IP address"):
        ApplicationSettings(bind_host=bind_host, bind_port=8000)
