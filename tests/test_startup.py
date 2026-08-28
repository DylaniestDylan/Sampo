from unittest.mock import Mock

from fastapi import FastAPI
from pytest import MonkeyPatch

import app.__main__ as application_main
from app.model_runtime import LlamaCppModelRuntime


def test_main_starts_fastapi_on_default_loopback(monkeypatch: MonkeyPatch) -> None:
    uvicorn_run = Mock()
    monkeypatch.setattr(application_main, "run_server", uvicorn_run)

    application_main.main()

    application = uvicorn_run.call_args.args[0]
    assert isinstance(application, FastAPI)
    assert isinstance(application.state.model_runtime, LlamaCppModelRuntime)
    assert application.state.generation_service is not None
    assert uvicorn_run.call_args.kwargs == {"host": "127.0.0.1", "port": 8000}
