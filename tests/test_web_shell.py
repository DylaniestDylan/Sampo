import asyncio
from html.parser import HTMLParser

from httpx import ASGITransport, AsyncClient

from app.main import create_app


class AssetReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        if tag == "link" and attributes.get("href"):
            self.references.append(attributes["href"])
        if tag == "script" and attributes.get("src"):
            self.references.append(attributes["src"])


async def request_local_web_assets():
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://localhost") as client:
        return (
            await client.get("/"),
            await client.get("/static/sampo.css"),
            await client.get("/static/alpine-3.16.3.min.js"),
        )


def test_local_web_shell_and_stylesheet_are_served() -> None:
    response, stylesheet_response, alpine_response = asyncio.run(
        request_local_web_assets()
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<h1>Sampo</h1>" in response.text
    assert "Local AI workspace" in response.text
    assert stylesheet_response.status_code == 200
    assert stylesheet_response.headers["content-type"].startswith("text/css")
    assert "font-family: system-ui" in stylesheet_response.text
    assert alpine_response.status_code == 200
    assert alpine_response.headers["content-type"].startswith("text/javascript")
    assert len(alpine_response.content) > 50_000


def test_shell_references_only_required_local_assets() -> None:
    response, _, _ = asyncio.run(request_local_web_assets())
    parser = AssetReferenceParser()
    parser.feed(response.text)

    assert parser.references == [
        "http://localhost/static/sampo.css",
        "http://localhost/static/alpine-3.16.3.min.js",
    ]
    assert all(reference.startswith("http://localhost/") for reference in parser.references)
