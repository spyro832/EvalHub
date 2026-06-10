"""Tests for the cost router and CostService."""

import pytest

from app.models.evaluation import EvalResult, Evaluation, EvaluationStatus


@pytest.mark.anyio
async def test_cost_summary_empty(client):
    """Cost summary with no data should return zeros."""
    response = await client.get("/api/v1/cost/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_usd"] == 0.0
    assert data["total_calls"] == 0
    assert data["total_input_tokens"] == 0
    assert data["total_output_tokens"] == 0


@pytest.mark.anyio
async def test_cost_summary_with_eval_result(client, db_session):
    """Cost summary should aggregate cost/token data from EvalResult rows."""
    # Insert a real Evaluation + EvalResult with cost data directly
    evaluation = Evaluation(
        name="Cost Test Eval",
        prompt="What is the capital of France?",
        status=EvaluationStatus.COMPLETED,
    )
    db_session.add(evaluation)
    await db_session.flush()

    result = EvalResult(
        evaluation_id=evaluation.id,
        model_config_id="cost-model-fake",
        response="Paris",
        cost_usd=0.0025,
        input_tokens=10,
        output_tokens=5,
    )
    db_session.add(result)
    await db_session.commit()

    response = await client.get("/api/v1/cost/summary")
    assert response.status_code == 200
    data = response.json()
    # Should now include our inserted data
    assert data["total_calls"] >= 1
    assert data["total_usd"] >= 0.0025
    assert data["total_input_tokens"] >= 10
    assert data["total_output_tokens"] >= 5
