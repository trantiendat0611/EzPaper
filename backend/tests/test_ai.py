from fastapi.testclient import TestClient


def test_ai_status_uses_local_provider_without_api_key(client: TestClient) -> None:
    response = client.get("/ai/status")
    assert response.status_code == 200
    body = response.json()
    assert body["has_openai_api_key"] is False
    assert body["active_provider"] == "local"
