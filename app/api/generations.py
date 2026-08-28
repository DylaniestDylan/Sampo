import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app.harness import MAX_HARNESS_CONTEXT_CHARS, PHASE_ONE_APPLICATION_POLICY
from app.workspace import (
    GenerationEvent,
    GenerationEventsAlreadyClaimedError,
    GenerationRegistryCapacityError,
    GenerationService,
    GenerationState,
)


MAX_API_PROMPT_CHARS = MAX_HARNESS_CONTEXT_CHARS - len(
    PHASE_ONE_APPLICATION_POLICY
)
MAX_SSE_EVENT_DATA_BYTES = 32_768

router = APIRouter(prefix="/api/generations")


class CreateGenerationRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=MAX_API_PROMPT_CHARS)

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("prompt must not be blank")
        return value


class CreateGenerationResponse(BaseModel):
    generation_id: str


class GenerationStatusResponse(BaseModel):
    generation_id: str
    status: str
    error: str | None


def _service(request: Request) -> GenerationService:
    service = request.app.state.generation_service
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="model runtime is not configured",
        )
    return service


def _status_response(state: GenerationState) -> GenerationStatusResponse:
    return GenerationStatusResponse(
        generation_id=state.generation_id,
        status=state.status.value,
        error=state.error,
    )


@router.post("", response_model=CreateGenerationResponse, status_code=202)
async def create_generation(
    payload: CreateGenerationRequest,
    request: Request,
) -> CreateGenerationResponse:
    try:
        state = _service(request).create_generation(payload.prompt)
    except GenerationRegistryCapacityError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return CreateGenerationResponse(generation_id=state.generation_id)


@router.get("/{generation_id}", response_model=GenerationStatusResponse)
async def generation_status(
    generation_id: str,
    request: Request,
) -> GenerationStatusResponse:
    state = _service(request).get_generation(generation_id)
    if state is None:
        raise HTTPException(status_code=404, detail="generation not found")
    return _status_response(state)


@router.get("/{generation_id}/events")
async def generation_events(
    generation_id: str,
    request: Request,
) -> StreamingResponse:
    service = _service(request)
    if service.get_generation(generation_id) is None:
        raise HTTPException(status_code=404, detail="generation not found")
    try:
        event_stream = service.stream_events(generation_id)
    except GenerationEventsAlreadyClaimedError as error:
        raise HTTPException(
            status_code=409,
            detail="generation event stream is already claimed",
        ) from error

    async def stream() -> AsyncIterator[str]:
        try:
            async for event in event_stream:
                yield _encode_sse(event, generation_id=generation_id)
        finally:
            await event_stream.aclose()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _encode_sse(event: GenerationEvent, *, generation_id: str) -> str:
    data: dict[str, str] = {"generation_id": generation_id}
    if event.text is not None:
        data["text"] = event.text
    if event.error is not None:
        data["error"] = event.error
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_SSE_EVENT_DATA_BYTES:
        raise RuntimeError("bounded generation event exceeded SSE payload limit")
    return f"event: {event.name.value}\ndata: {encoded}\n\n"
