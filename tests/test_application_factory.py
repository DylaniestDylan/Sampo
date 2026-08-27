from fastapi import FastAPI

from app.main import create_app


def test_create_app_returns_fastapi_application() -> None:
    application = create_app()

    assert isinstance(application, FastAPI)
