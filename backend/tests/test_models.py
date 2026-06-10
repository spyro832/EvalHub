import pytest


@pytest.mark.anyio
async def test_list_models(client):
    """GET /models returns a valid list (may be non-empty due to test ordering)."""
    response = await client.get("/api/v1/models")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_create_model(client):
    payload = {
        "name": "GPT-4o",
        "provider": "openai",
        "model_id": "gpt-4o",
        "api_key": "sk-test-key",
    }
    response = await client.post("/api/v1/models", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "GPT-4o"
    assert data["provider"] == "openai"
    assert data["model_id"] == "gpt-4o"
    assert "api_key" not in data  # key must not be returned


@pytest.mark.anyio
async def test_create_model_validation_error(client):
    response = await client.post("/api/v1/models", json={"name": ""})
    assert response.status_code == 422
