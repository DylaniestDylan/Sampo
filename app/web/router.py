from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from app.web.templates import STATIC_DIRECTORY, templates


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def workspace_shell(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="shell.html",
        context={"csrf_token": request.app.state.csrf_token},
    )


@router.get("/static/sampo.css", name="static_stylesheet")
async def static_stylesheet() -> Response:
    return Response(
        content=(STATIC_DIRECTORY / "sampo.css").read_bytes(),
        media_type="text/css",
    )


@router.get("/static/alpine-3.16.3.min.js", name="static_alpine")
async def static_alpine() -> Response:
    return Response(
        content=(STATIC_DIRECTORY / "alpine-3.16.3.min.js").read_bytes(),
        media_type="text/javascript",
    )
