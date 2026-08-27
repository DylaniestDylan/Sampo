from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
async def process_health() -> dict[str, str]:
    return {"status": "ok"}
