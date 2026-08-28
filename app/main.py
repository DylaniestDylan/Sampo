from secrets import token_urlsafe

from fastapi import FastAPI

from app.api.generations import router as generations_router
from app.api.health import router as health_router
from app.harness import (
    PHASE_ONE_APPLICATION_POLICY,
    ApplicationHarness,
    HarnessPolicy,
    HarnessToolBoundary,
    ToolRegistry,
)
from app.model_runtime import ModelRuntime
from app.workspace import GenerationService
from app.web.router import router as web_router
from app.web.security import (
    BrowserMutationProtectionMiddleware,
    TrustedLocalHostMiddleware,
)


def create_app(*, model_runtime: ModelRuntime | None = None) -> FastAPI:
    application = FastAPI()
    application.state.csrf_token = token_urlsafe(32)
    application.state.model_runtime = model_runtime
    application.state.generation_service = (
        GenerationService(
            harness=ApplicationHarness(
                runtime=model_runtime,
                policy=HarnessPolicy(
                    application_text=PHASE_ONE_APPLICATION_POLICY
                ),
                tool_boundary=HarnessToolBoundary(registry=ToolRegistry()),
            )
        )
        if model_runtime is not None
        else None
    )
    application.include_router(health_router)
    application.include_router(generations_router)
    application.include_router(web_router)
    application.add_middleware(
        BrowserMutationProtectionMiddleware,
        csrf_token=application.state.csrf_token,
    )
    application.add_middleware(TrustedLocalHostMiddleware)
    return application
