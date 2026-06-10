"""Tests for the evaluations router and EvalService."""

from unittest.mock import MagicMock, patch

import pytest


async def test_list_evaluations(client):
    response = await client.get("/api/v1/evaluations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_get_evaluation_not_found(client):
    response = await client.get("/api/v1/evaluations/nonexistent-id")
    assert response.status_code == 404


async def test_create_evaluation_pending(client):
    """POST /evaluations should dispatch a Celery task and return status=pending."""
    payload = {
        "name": "My Eval",
        "prompt": "What is 2+2?",
        "model_ids": ["fake-model-1"],
    }
    # Patch the Celery task so it doesn't actually run
    mock_task = MagicMock()
    mock_task.delay = MagicMock(return_value=None)

    with patch("app.tasks.eval_tasks.run_evaluation", mock_task):
        response = await client.post("/api/v1/evaluations", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Eval"
    assert data["prompt"] == "What is 2+2?"
    assert data["status"] == "pending"
    assert "id" in data
    # Celery dispatch was called
    mock_task.delay.assert_called_once_with(data["id"])


async def test_get_evaluation_after_create(client):
    """GET /{id} should return the evaluation created above."""
    mock_task = MagicMock()
    mock_task.delay = MagicMock(return_value=None)

    with patch("app.tasks.eval_tasks.run_evaluation", mock_task):
        create_resp = await client.post(
            "/api/v1/evaluations",
            json={"name": "Get Test", "prompt": "Hello", "model_ids": ["fake-model-x"]},
        )

    eval_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/evaluations/{eval_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == eval_id
    assert get_resp.json()["name"] == "Get Test"


async def test_list_evaluations_after_create(client):
    """GET /evaluations should include evaluations; list grows after a POST."""
    resp_before = await client.get("/api/v1/evaluations")
    count_before = len(resp_before.json())

    mock_task = MagicMock()
    mock_task.delay = MagicMock(return_value=None)
    with patch("app.tasks.eval_tasks.run_evaluation", mock_task):
        await client.post(
            "/api/v1/evaluations",
            json={"name": "Count Test", "prompt": "ping", "model_ids": ["fake-model-z"]},
        )

    resp_after = await client.get("/api/v1/evaluations")
    assert len(resp_after.json()) == count_before + 1


async def test_list_evaluations_pagination(client):
    """limit and skip query params should work."""
    response = await client.get("/api/v1/evaluations?limit=1&skip=0")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert len(items) <= 1
