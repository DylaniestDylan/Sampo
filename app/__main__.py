from uvicorn import run as run_server

from app.main import create_app
from app.settings import ApplicationSettings


def main() -> None:
    settings = ApplicationSettings(bind_port=8000)
    run_server(
        create_app(),
        host=settings.bind_host,
        port=settings.bind_port,
    )


if __name__ == "__main__":
    main()
