import pytest


@pytest.mark.anyio
async def test_list_benchmarks_empty(client):
    response = await client.get("/api/v1/benchmarks")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_create_benchmark_no_items(client):
    payload = {"name": "Empty Bench", "category": "coding"}
    response = await client.post("/api/v1/benchmarks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Empty Bench"
    assert data["item_count"] == 0
    assert data["items"] == []


@pytest.mark.anyio
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


@pytest.mark.anyio
async def test_get_benchmark_not_found(client):
    response = await client.get("/api/v1/benchmarks/nonexistent")
    assert response.status_code == 404


@pytest.mark.anyio
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


@pytest.mark.anyio
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


@pytest.mark.anyio
async def test_delete_benchmark(client):
    create = await client.post("/api/v1/benchmarks", json={"name": "To Delete"})
    bench_id = create.json()["id"]

    delete = await client.delete(f"/api/v1/benchmarks/{bench_id}")
    assert delete.status_code == 204

    get = await client.get(f"/api/v1/benchmarks/{bench_id}")
    assert get.status_code == 404
