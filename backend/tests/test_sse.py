"""
Tests for SSE streaming endpoints.

We use already-COMPLETED evaluations / runs so the generator exits after
the first iteration (no 1-second sleep), keeping tests fast.
"""

import json

import pytest

from app.models.evaluation import EvalResult, Evaluation, EvaluationStatus
from app.models.model_config import ModelConfig
from app.models.test_suite import TestRun, TestRunStatus, TestSuite

# ── Helpers ───────────────────────────────────────────────────────────────────


async def _first_sse_event(response_text: str) -> dict:
    """Parse the first SSE data line from a streaming response body."""
    for line in response_text.splitlines():
        if line.startswith("data:"):
            return json.loads(line[len("data:"):].strip())
    raise AssertionError(f"No SSE data line found in:\n{response_text}")


# ── Evaluation stream ─────────────────────────────────────────────────────────


async def test_stream_evaluation_not_found(client):
    """Stream for a non-existent evaluation_id → error SSE event."""
    response = await client.get("/api/v1/evaluations/nonexistent-eval/stream")
    assert response.status_code == 200  # SSE always returns 200 (errors are in-band)
    event = await _first_sse_event(response.text)
    assert "error" in event


async def test_stream_evaluation_completed(client, db_session):
    """
    Stream for a COMPLETED evaluation → single SSE event with status=completed,
    then generator closes (no sleep needed).
    """
    evaluation = Evaluation(
        id="sse-eval-1",
        name="SSE Test Eval",
        prompt="hello",
        status=EvaluationStatus.COMPLETED,
    )
    db_session.add(evaluation)
    await db_session.flush()

    # Add a completed EvalResult so completed_count > 0
    model = ModelConfig(
        id="sse-model-1", name="SSE Model", provider="openai", model_id="gpt-4o"
    )
    db_session.add(model)
    await db_session.flush()

    result = EvalResult(
        evaluation_id="sse-eval-1",
        model_config_id="sse-model-1",
        response="World",
    )
    db_session.add(result)
    await db_session.commit()

    response = await client.get("/api/v1/evaluations/sse-eval-1/stream")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    event = await _first_sse_event(response.text)
    assert event["id"] == "sse-eval-1"
    assert event["status"] == "completed"
    assert event["completed"] == 1
    assert event["total"] == 1


# ── Test-suite run stream ─────────────────────────────────────────────────────


async def test_stream_run_not_found(client):
    """Stream for a non-existent run_id → error SSE event."""
    # Suite ID doesn't matter for the stream endpoint validation
    response = await client.get("/api/v1/test-suites/any-suite/runs/nonexistent-run/stream")
    assert response.status_code == 200
    event = await _first_sse_event(response.text)
    assert "error" in event


async def test_stream_run_completed(client, db_session):
    """
    Stream for a COMPLETED run → single SSE event with status=completed,
    then generator closes immediately (no sleep).
    """
    suite = TestSuite(id="sse-suite-1", name="SSE Suite")
    db_session.add(suite)
    await db_session.flush()

    run = TestRun(
        id="sse-run-1",
        suite_id="sse-suite-1",
        model_config_id="sse-model-1",  # FK not enforced in SQLite test
        status=TestRunStatus.COMPLETED,
        pass_count=3,
        fail_count=1,
    )
    db_session.add(run)
    await db_session.commit()

    response = await client.get("/api/v1/test-suites/sse-suite-1/runs/sse-run-1/stream")
    assert response.status_code == 200

    event = await _first_sse_event(response.text)
    assert event["run_id"] == "sse-run-1"
    assert event["status"] == "completed"
    assert event["pass_count"] == 3
    assert event["fail_count"] == 1
