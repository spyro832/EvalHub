import pytest

from app.services.model_utils import get_litellm_model_id, score_response


def test_ollama_prefix_added():
    assert get_litellm_model_id("ollama", "llama3.2") == "ollama/llama3.2"


def test_ollama_prefix_not_doubled():
    assert get_litellm_model_id("ollama", "ollama/llama3.2") == "ollama/llama3.2"


def test_openai_no_prefix():
    assert get_litellm_model_id("openai", "gpt-4o") == "gpt-4o"


def test_anthropic_no_prefix():
    assert (
        get_litellm_model_id("anthropic", "claude-3-5-sonnet-20241022")
        == "claude-3-5-sonnet-20241022"
    )


def test_huggingface_prefix_added():
    assert get_litellm_model_id("huggingface", "starcoder") == "huggingface/starcoder"


def test_score_response_expected_output_match():
    assert score_response("The capital is Paris.", "Paris", None) is True


def test_score_response_expected_output_no_match():
    assert score_response("Berlin is in Germany.", "Paris", None) is False


def test_score_response_tags_all_match():
    assert score_response("def foo(): return True", None, "def,return") is True


def test_score_response_tags_partial_no_match():
    assert score_response("def foo(): pass", None, "def,return") is False


def test_score_response_no_criteria_non_empty():
    assert score_response("anything", None, None) is True


def test_score_response_no_criteria_empty():
    assert score_response("  ", None, None) is False


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
