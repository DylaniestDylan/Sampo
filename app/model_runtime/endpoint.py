from ipaddress import ip_address
from urllib.parse import urlsplit


def validate_local_runtime_endpoint(endpoint: str) -> str:
    parsed = urlsplit(endpoint)
    if (
        parsed.scheme != "http"
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "runtime_endpoint must be an HTTP URL for a numeric loopback IP"
        )
    hostname = parsed.hostname
    assert hostname is not None
    try:
        address = ip_address(hostname)
        port = parsed.port
    except ValueError as error:
        raise ValueError(
            "runtime_endpoint must be an HTTP URL for a numeric loopback IP"
        ) from error
    if not address.is_loopback or port is None:
        raise ValueError(
            "runtime_endpoint must be an HTTP URL for a numeric loopback IP"
        )
    return endpoint.rstrip("/")
