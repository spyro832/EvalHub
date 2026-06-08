import pytest

from app.services.eval_service import _get_litellm_model_id


def test_ollama_prefix_added():
    assert _get_litellm_model_id("ollama", "llama3.2") == "ollama/llama3.2"


def test_ollama_prefix_not_doubled():
    assert _get_litellm_model_id("ollama", "ollama/llama3.2") == "ollama/llama3.2"


def test_openai_no_prefix():
    assert _get_litellm_model_id("openai", "gpt-4o") == "gpt-4o"


def test_anthropic_no_prefix():
    assert _get_litellm_model_id("anthropic", "claude-3-5-sonnet-20241022") == "claude-3-5-sonnet-20241022"


def test_huggingface_prefix_added():
    assert _get_litellm_model_id("huggingface", "starcoder") == "huggingface/starcoder"


@pytest.mark.anyio
async def test_create_model_no_api_key(client):
    payload = {
        "name": "Ollama Local",
        "provider": "ollama",
        "model_id": "llama3.2",
        "base_url": "http://localhost:11434",
        "is_local": True,
    }
    response = await client.post("/api/v1/models", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["is_local"] is True
    assert "api_key" not in data


@pytest.mark.anyio
async def test_delete_model_not_found(client):
    response = await client.delete("/api/v1/models/nonexistent-id")
    assert response.status_code == 404
