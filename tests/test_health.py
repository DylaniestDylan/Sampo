import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import create_app


async def request_health():
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get("/health")


def test_health_reports_sampo_process_health() -> None:
    response = asyncio.run(request_health())

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
