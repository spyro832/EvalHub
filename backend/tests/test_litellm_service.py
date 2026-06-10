"""
Unit tests for LiteLLMService — mock litellm.completion so no real API calls happen.
"""

from unittest.mock import MagicMock, patch

from app.services.litellm_service import LiteLLMService


def _mock_completion_response(content: str = "Hello!", prompt_tokens: int = 10, completion_tokens: int = 20):
    """Build a minimal litellm completion response mock."""
    msg = MagicMock()
    msg.content = content

    choice = MagicMock()
    choice.message = msg

    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens

    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    return resp


def test_call_model_basic():
    """call_model() should return a ModelCallResult with correct fields."""
    mock_resp = _mock_completion_response("The answer is 42.", 8, 6)

    with (
        patch("app.services.litellm_service.completion", return_value=mock_resp),
        patch("app.services.litellm_service.litellm.completion_cost", return_value=0.0012),
    ):
        svc = LiteLLMService()
        result = svc.call_model("gpt-4o", "What is 6×7?")

    assert result.response == "The answer is 42."
    assert result.input_tokens == 8
    assert result.output_tokens == 6
    assert abs(result.cost_usd - 0.0012) < 1e-9
    assert result.latency_ms >= 0
    assert result.model_id == "gpt-4o"


def test_call_model_with_api_key():
    """api_key should be forwarded to litellm.completion kwargs."""
    mock_resp = _mock_completion_response("OK")

    captured_kwargs = {}

    def capture(**kwargs):
        captured_kwargs.update(kwargs)
        return mock_resp

    with (
        patch("app.services.litellm_service.completion", side_effect=capture),
        patch("app.services.litellm_service.litellm.completion_cost", return_value=0.0),
    ):
        svc = LiteLLMService()
        svc.call_model("gpt-4o", "Hello", api_key="sk-secret")

    assert captured_kwargs.get("api_key") == "sk-secret"


def test_call_model_with_base_url():
    """base_url should be forwarded for local/Ollama models."""
    mock_resp = _mock_completion_response("Hi")

    captured_kwargs = {}

    def capture(**kwargs):
        captured_kwargs.update(kwargs)
        return mock_resp

    with (
        patch("app.services.litellm_service.completion", side_effect=capture),
        patch("app.services.litellm_service.litellm.completion_cost", return_value=0.0),
    ):
        svc = LiteLLMService()
        svc.call_model("ollama/llama3", "Hello", base_url="http://localhost:11434")

    assert captured_kwargs.get("base_url") == "http://localhost:11434"


def test_call_model_zero_cost_when_cost_is_none():
    """If completion_cost returns None, cost_usd should be 0.0."""
    mock_resp = _mock_completion_response()

    with (
        patch("app.services.litellm_service.completion", return_value=mock_resp),
        patch("app.services.litellm_service.litellm.completion_cost", return_value=None),
    ):
        svc = LiteLLMService()
        result = svc.call_model("gpt-4o", "Hello")

    assert result.cost_usd == 0.0
