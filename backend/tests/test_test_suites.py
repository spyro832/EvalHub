import pytest


@pytest.mark.anyio
async def test_list_test_suites_empty(client):
    response = await client.get("/api/v1/test-suites")
    assert response.status_code == 200
    assert response.json() == []


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
