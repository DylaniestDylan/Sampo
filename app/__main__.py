from uvicorn import run as run_server

from app.main import create_app
from app.model_runtime import LlamaCppModelRuntime
from app.settings import ApplicationSettings


def main() -> None:
    settings = ApplicationSettings(bind_port=8000)
    runtime = LlamaCppModelRuntime(
        endpoint=settings.runtime_endpoint,
        model=settings.runtime_model,
    )
    run_server(
        create_app(model_runtime=runtime),
        host=settings.bind_host,
        port=settings.bind_port,
    )


if __name__ == "__main__":
    main()
