"""
Unit tests for EvalService._run_single_model — mock LiteLLM so no real API calls.
"""

from unittest.mock import patch

import pytest

from app.models.model_config import ModelConfig
from app.services.eval_service import EvalService
from app.services.litellm_service import ModelCallResult


def _fake_call_result(response: str = "Paris") -> ModelCallResult:
    return ModelCallResult(
        response=response,
        latency_ms=50,
        input_tokens=8,
        output_tokens=4,
        cost_usd=0.0005,
        model_id="gpt-4o",
    )


async def test_run_single_model_not_found(db_session):
    """_run_single_model with a non-existent model_config_id returns an error EvalResult."""
    svc = EvalService(db_session)
    result = await svc._run_single_model("fake-eval-id", "nonexistent-model-xyz", "Hello")

    assert result.evaluation_id == "fake-eval-id"
    assert result.model_config_id == "nonexistent-model-xyz"
    assert result.error is not None
    assert "not found" in result.error.lower()
    assert result.response is None


async def test_run_single_model_success(db_session):
    """_run_single_model with a valid model and mocked LiteLLM returns a filled EvalResult."""
    model = ModelConfig(
        id="svc-eval-m1",
        name="Test Model",
        provider="openai",
        model_id="gpt-4o",
    )
    db_session.add(model)
    await db_session.commit()

    svc = EvalService(db_session)
    with patch.object(svc.llm, "call_model", return_value=_fake_call_result("The capital is Paris.")):
        result = await svc._run_single_model("fake-eval-id", "svc-eval-m1", "Capital of France?")

    assert result.response == "The capital is Paris."
    assert result.latency_ms == 50
    assert result.input_tokens == 8
    assert result.output_tokens == 4
    assert abs(result.cost_usd - 0.0005) < 1e-9
    assert result.error is None


async def test_run_single_model_llm_exception(db_session):
    """If LiteLLM raises, _run_single_model returns an error EvalResult."""
    model = ModelConfig(
        id="svc-eval-m2",
        name="Error Model",
        provider="openai",
        model_id="gpt-4o",
    )
    db_session.add(model)
    await db_session.commit()

    svc = EvalService(db_session)
    with patch.object(svc.llm, "call_model", side_effect=RuntimeError("Rate limit exceeded")):
        result = await svc._run_single_model("fake-eval-id", "svc-eval-m2", "Hello")

    assert result.error == "Rate limit exceeded"
    assert result.response is None


async def test_run_single_model_with_encrypted_api_key(db_session):
    """If the model has an encrypted api_key, it should be decrypted and forwarded."""
    from app.core.security import encrypt_api_key

    model = ModelConfig(
        id="svc-eval-m3",
        name="Keyed Model",
        provider="openai",
        model_id="gpt-4o",
        api_key_encrypted=encrypt_api_key("sk-test-secret"),
    )
    db_session.add(model)
    await db_session.commit()

    captured = {}

    def capture_call(**kwargs):
        captured.update(kwargs)
        return _fake_call_result("OK")

    svc = EvalService(db_session)
    with patch.object(svc.llm, "call_model", side_effect=capture_call):
        result = await svc._run_single_model("fake-eval-id", "svc-eval-m3", "Hello")

    assert result.response == "OK"
    assert captured.get("api_key") is not None  # key was decrypted and passed through


async def test_create_evaluation_blocking(db_session):
    """
    create_evaluation() (the older synchronous-flow method) should return a
    COMPLETED evaluation after running all models.
    """
    from app.models.evaluation import EvalResult, EvaluationStatus
    from app.schemas.evaluation import EvaluationCreate

    data = EvaluationCreate(name="Block Eval", prompt="What is 1+1?", model_ids=["fake-model-b"])

    # Pre-build a fake EvalResult that _run_single_model would return
    fake_result = EvalResult(
        evaluation_id="placeholder",  # will be overwritten in create_evaluation
        model_config_id="fake-model-b",
        response="2",
    )

    svc = EvalService(db_session)
    with patch.object(svc, "_run_single_model", return_value=fake_result):
        evaluation = await svc.create_evaluation(data)

    assert evaluation.status == EvaluationStatus.COMPLETED
    assert evaluation.name == "Block Eval"
    assert evaluation.prompt == "What is 1+1?"
