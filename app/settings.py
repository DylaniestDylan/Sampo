from dataclasses import dataclass
from ipaddress import ip_address

from app.model_runtime.endpoint import validate_local_runtime_endpoint


@dataclass(kw_only=True)
class ApplicationSettings:
    bind_host: str = "127.0.0.1"
    bind_port: int
    runtime_endpoint: str = "http://127.0.0.1:8080"
    runtime_model: str = "local-model"

    def __post_init__(self) -> None:
        try:
            address = ip_address(self.bind_host)
        except ValueError as error:
            raise ValueError(
                "bind_host must be a numeric loopback IP address"
            ) from error

        if not address.is_loopback:
            raise ValueError("bind_host must be a numeric loopback IP address")

        if not self.runtime_endpoint.strip():
            raise ValueError("runtime_endpoint must not be blank")
        if not self.runtime_model.strip():
            raise ValueError("runtime_model must not be blank")

        validate_local_runtime_endpoint(self.runtime_endpoint)
