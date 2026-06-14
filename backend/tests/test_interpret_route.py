import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.routers.interpret import get_llm_client


class FakeLLMClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    async def interpret(self, text: str, elements: list[dict]) -> dict:
        return self.payload


@pytest.mark.anyio
async def test_interpret_returns_sanitized_commands() -> None:
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient(
        {
            "commands": [
                {
                    "action": "add",
                    "id": "el_1",
                    "tag": "circle",
                    "attrs": {"cx": 120, "cy": 120, "r": 30, "fill": "red"},
                    "text": None,
                }
            ],
            "reply": "已完成。",
        }
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/interpret", json={"text": "draw a red circle", "elements": []})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["commands"][0]["tag"] == "circle"
    assert body["reply"] == "已完成。"


@pytest.mark.anyio
async def test_interpret_skips_unsafe_single_command() -> None:
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient(
        {
            "commands": [
                {"action": "add", "id": "el_1", "tag": "script", "attrs": {}, "text": None},
                {"action": "clear"},
            ],
            "reply": "已清空。",
        }
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/interpret", json={"text": "clear", "elements": []})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert [command["action"] for command in body["commands"]] == ["clear"]
    assert body["warnings"]


@pytest.mark.anyio
async def test_interpret_invalid_schema_returns_bad_gateway() -> None:
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient({"commands": [{"action": "add"}]})

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/interpret", json={"text": "draw", "elements": []})

    app.dependency_overrides.clear()

    assert response.status_code == 502
