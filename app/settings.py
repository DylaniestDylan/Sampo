from dataclasses import dataclass
from ipaddress import ip_address


@dataclass(kw_only=True)
class ApplicationSettings:
    bind_host: str = "127.0.0.1"
    bind_port: int

    def __post_init__(self) -> None:
        try:
            address = ip_address(self.bind_host)
        except ValueError as error:
            raise ValueError(
                "bind_host must be a numeric loopback IP address"
            ) from error

        if not address.is_loopback:
            raise ValueError("bind_host must be a numeric loopback IP address")
