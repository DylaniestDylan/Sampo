from secrets import token_urlsafe

from fastapi import FastAPI

from app.api.health import router as health_router
from app.model_runtime import ModelRuntime
from app.web.router import router as web_router
from app.web.security import (
    BrowserMutationProtectionMiddleware,
    TrustedLocalHostMiddleware,
)


def create_app(*, model_runtime: ModelRuntime | None = None) -> FastAPI:
    application = FastAPI()
    application.state.csrf_token = token_urlsafe(32)
    application.state.model_runtime = model_runtime
    application.include_router(health_router)
    application.include_router(web_router)
    application.add_middleware(
        BrowserMutationProtectionMiddleware,
        csrf_token=application.state.csrf_token,
    )
    application.add_middleware(TrustedLocalHostMiddleware)
    return application
