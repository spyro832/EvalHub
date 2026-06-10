from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.anyio
async def test_list_test_suites(client):
    """GET /test-suites returns a valid list (may be non-empty due to test ordering)."""
    response = await client.get("/api/v1/test-suites")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_create_test_suite_no_cases(client):
    payload = {"name": "My Suite", "description": "A test suite", "category": "coding"}
    response = await client.post("/api/v1/test-suites", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Suite"
    assert data["category"] == "coding"
    assert data["cases"] == []


@pytest.mark.anyio
async def test_create_test_suite_with_cases(client):
    payload = {
        "name": "Python Suite",
        "cases": [
            {"input": "Write a palindrome checker", "expected_tags": "python,def"},
            {"input": "Write a fibonacci function", "expected_output": "def fibonacci"},
        ],
    }
    response = await client.post("/api/v1/test-suites", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert len(data["cases"]) == 2


@pytest.mark.anyio
async def test_get_test_suite_not_found(client):
    response = await client.get("/api/v1/test-suites/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_test_suite(client):
    create = await client.post("/api/v1/test-suites", json={"name": "To Delete"})
    suite_id = create.json()["id"]

    delete = await client.delete(f"/api/v1/test-suites/{suite_id}")
    assert delete.status_code == 204

    get = await client.get(f"/api/v1/test-suites/{suite_id}")
    assert get.status_code == 404


@pytest.mark.anyio
async def test_get_test_suite(client):
    """GET /{suite_id} for an existing suite should return 200."""
    create = await client.post(
        "/api/v1/test-suites",
        json={"name": "Fetch Me", "description": "desc", "category": "coding"},
    )
    suite_id = create.json()["id"]

    get = await client.get(f"/api/v1/test-suites/{suite_id}")
    assert get.status_code == 200
    assert get.json()["name"] == "Fetch Me"
    assert get.json()["category"] == "coding"


# ── Run endpoint ──────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_run_test_suite_suite_not_found(client):
    """POST /{id}/run with a non-existent suite → 404."""
    model_resp = await client.post(
        "/api/v1/models",
        json={"name": "Suite Runner Model", "provider": "openai", "model_id": "gpt-4o"},
    )
    model_id = model_resp.json()["id"]

    response = await client.post(
        "/api/v1/test-suites/nonexistent-suite/run",
        json={"model_config_id": model_id},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_run_test_suite_success(client):
    """POST /{id}/run should create a TestRun (PENDING) and dispatch Celery task."""
    # Create suite
    suite_resp = await client.post(
        "/api/v1/test-suites",
        json={
            "name": "Runnable Suite",
            "cases": [{"input": "Write hello world", "expected_tags": "print"}],
        },
    )
    suite_id = suite_resp.json()["id"]

    # Create model config
    model_resp = await client.post(
        "/api/v1/models",
        json={"name": "Run Model", "provider": "openai", "model_id": "gpt-4o"},
    )
    model_id = model_resp.json()["id"]

    mock_task = MagicMock()
    mock_task.delay = MagicMock(return_value=None)

    with patch("app.tasks.eval_tasks.run_test_suite_task", mock_task):
        response = await client.post(
            f"/api/v1/test-suites/{suite_id}/run",
            json={"model_config_id": model_id},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["suite_id"] == suite_id
    assert data["model_config_id"] == model_id
    assert data["status"] == "pending"
    # Celery task was dispatched
    mock_task.delay.assert_called_once_with(data["id"])


# ── List runs endpoint ────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_list_runs_empty(client):
    """GET /{suite_id}/runs for a suite with no runs → empty list."""
    create = await client.post("/api/v1/test-suites", json={"name": "No Runs Suite"})
    suite_id = create.json()["id"]

    response = await client.get(f"/api/v1/test-suites/{suite_id}/runs")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_delete_test_suite_not_found(client):
    """DELETE on a nonexistent suite → 404."""
    response = await client.delete("/api/v1/test-suites/nonexistent-suite-id")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_list_runs_after_trigger(client):
    """GET /{suite_id}/runs should include runs created by POST /{suite_id}/run."""
    suite_resp = await client.post(
        "/api/v1/test-suites",
        json={"name": "List Runs Suite"},
    )
    suite_id = suite_resp.json()["id"]

    model_resp = await client.post(
        "/api/v1/models",
        json={"name": "List Runs Model", "provider": "openai", "model_id": "gpt-4o"},
    )
    model_id = model_resp.json()["id"]

    mock_task = MagicMock()
    mock_task.delay = MagicMock(return_value=None)

    with patch("app.tasks.eval_tasks.run_test_suite_task", mock_task):
        await client.post(
            f"/api/v1/test-suites/{suite_id}/run",
            json={"model_config_id": model_id},
        )

    list_resp = await client.get(f"/api/v1/test-suites/{suite_id}/runs")
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert len(runs) == 1
    assert runs[0]["suite_id"] == suite_id
