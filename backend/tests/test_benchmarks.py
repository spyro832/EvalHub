from unittest.mock import patch

import pytest

from app.services.litellm_service import ModelCallResult

# ── Fixture for a reusable mocked LLM call result ─────────────────────────────

def _mock_call_result(response: str = "42") -> ModelCallResult:
    return ModelCallResult(
        response=response,
        latency_ms=123,
        input_tokens=10,
        output_tokens=5,
        cost_usd=0.001,
        model_id="gpt-4o",
    )


async def test_list_benchmarks_empty(client):
    response = await client.get("/api/v1/benchmarks")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_benchmark_no_items(client):
    payload = {"name": "Empty Bench", "category": "coding"}
    response = await client.post("/api/v1/benchmarks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Empty Bench"
    assert data["item_count"] == 0
    assert data["items"] == []


async def test_create_benchmark_with_items(client):
    payload = {
        "name": "Python Bench",
        "category": "coding",
        "author": "Test",
        "items": [
            {"input": "Write a palindrome checker", "expected_tags": "def,return"},
            {"input": "What is 2+2?", "expected_output": "4"},
        ],
    }
    response = await client.post("/api/v1/benchmarks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["item_count"] == 2
    assert len(data["items"]) == 2


async def test_get_benchmark_not_found(client):
    response = await client.get("/api/v1/benchmarks/nonexistent")
    assert response.status_code == 404


async def test_import_benchmark(client):
    payload = {
        "name": "Imported Bench",
        "category": "rag",
        "items": [{"input": "What is the capital of France?", "expected_output": "Paris"}],
    }
    response = await client.post("/api/v1/benchmarks/import", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Imported Bench"
    assert data["item_count"] == 1


async def test_export_benchmark(client):
    # Create first
    create = await client.post(
        "/api/v1/benchmarks",
        json={
            "name": "Export Test",
            "items": [{"input": "Hello?", "expected_output": "hi"}],
        },
    )
    bench_id = create.json()["id"]

    export = await client.get(f"/api/v1/benchmarks/{bench_id}/export")
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("application/json")
    body = export.json()
    assert body["name"] == "Export Test"
    assert len(body["items"]) == 1


async def test_delete_benchmark(client):
    create = await client.post("/api/v1/benchmarks", json={"name": "To Delete"})
    bench_id = create.json()["id"]

    delete = await client.delete(f"/api/v1/benchmarks/{bench_id}")
    assert delete.status_code == 204

    get = await client.get(f"/api/v1/benchmarks/{bench_id}")
    assert get.status_code == 404


# ── Run endpoint ──────────────────────────────────────────────────────────────


async def test_run_benchmark_not_found(client):
    """POST /{id}/run with a non-existent benchmark ID → 404."""
    response = await client.post(
        "/api/v1/benchmarks/nonexistent-bench/run",
        json={"model_config_id": "any-model"},
    )
    assert response.status_code == 404


async def test_run_benchmark_model_not_found(client):
    """POST /{id}/run with a valid benchmark but non-existent model → 404."""
    create = await client.post(
        "/api/v1/benchmarks",
        json={"name": "Run Model 404 Bench", "items": [{"input": "2+2?", "expected_output": "4"}]},
    )
    bench_id = create.json()["id"]

    response = await client.post(
        f"/api/v1/benchmarks/{bench_id}/run",
        json={"model_config_id": "nonexistent-model"},
    )
    assert response.status_code == 404


async def test_run_benchmark_success(client):
    """POST /{id}/run should call LiteLLM per item and return pass/fail stats."""
    # 1. Create a model config
    model_resp = await client.post(
        "/api/v1/models",
        json={"name": "Bench Runner", "provider": "openai", "model_id": "gpt-4o"},
    )
    assert model_resp.status_code == 201
    model_id = model_resp.json()["id"]

    # 2. Create a benchmark with two items
    bench_resp = await client.post(
        "/api/v1/benchmarks",
        json={
            "name": "Run Bench",
            "items": [
                {"input": "What is 2+2?", "expected_output": "4"},
                {"input": "Write a python function", "expected_tags": "def"},
            ],
        },
    )
    assert bench_resp.status_code == 201
    bench_id = bench_resp.json()["id"]

    # 3. Mock LiteLLM so we don't hit real APIs
    with patch("app.routers.benchmarks._llm.call_model") as mock_llm:
        mock_llm.side_effect = [
            _mock_call_result("4"),        # item 1: matches expected_output "4"
            _mock_call_result("def foo():"), # item 2: matches tag "def"
        ]
        response = await client.post(
            f"/api/v1/benchmarks/{bench_id}/run",
            json={"model_config_id": model_id},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["benchmark_id"] == bench_id
    assert data["model_config_id"] == model_id
    assert data["total_items"] == 2
    assert data["pass_count"] == 2
    assert data["fail_count"] == 0
    assert data["pass_rate"] == 1.0
    assert len(data["results"]) == 2
    assert all(r["passed"] for r in data["results"])


async def test_run_benchmark_with_item_limit(client):
    """item_limit param should restrict how many items are evaluated."""
    model_resp = await client.post(
        "/api/v1/models",
        json={"name": "Bench Limit Model", "provider": "openai", "model_id": "gpt-4o"},
    )
    model_id = model_resp.json()["id"]

    bench_resp = await client.post(
        "/api/v1/benchmarks",
        json={
            "name": "Limit Bench",
            "items": [
                {"input": "Q1", "expected_output": "A1"},
                {"input": "Q2", "expected_output": "A2"},
                {"input": "Q3", "expected_output": "A3"},
            ],
        },
    )
    bench_id = bench_resp.json()["id"]

    with patch("app.routers.benchmarks._llm.call_model") as mock_llm:
        mock_llm.return_value = _mock_call_result("A1")
        response = await client.post(
            f"/api/v1/benchmarks/{bench_id}/run",
            json={"model_config_id": model_id, "item_limit": 1},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 1
    mock_llm.assert_called_once()


async def test_run_benchmark_llm_error(client):
    """If LiteLLM raises, the item should fail gracefully."""
    model_resp = await client.post(
        "/api/v1/models",
        json={"name": "Bench Error Model", "provider": "openai", "model_id": "gpt-4o"},
    )
    model_id = model_resp.json()["id"]

    bench_resp = await client.post(
        "/api/v1/benchmarks",
        json={
            "name": "Error Bench",
            "items": [{"input": "Fail me", "expected_output": "never"}],
        },
    )
    bench_id = bench_resp.json()["id"]

    with patch("app.routers.benchmarks._llm.call_model", side_effect=RuntimeError("API timeout")):
        response = await client.post(
            f"/api/v1/benchmarks/{bench_id}/run",
            json={"model_config_id": model_id},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["pass_count"] == 0
    assert data["fail_count"] == 1
    assert "ERROR:" in data["results"][0]["response"]
