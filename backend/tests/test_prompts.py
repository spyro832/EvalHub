import pytest


@pytest.mark.anyio
async def test_list_prompts_empty(client):
    response = await client.get("/api/v1/prompts")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_create_and_get_prompt(client):
    payload = {"name": "Test Prompt", "content": "Say hello to {name}", "tags": "test,hello"}
    response = await client.post("/api/v1/prompts", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Prompt"
    assert data["content"] == "Say hello to {name}"
    assert data["tags"] == "test,hello"
    prompt_id = data["id"]

    get_response = await client.get(f"/api/v1/prompts/{prompt_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == prompt_id


@pytest.mark.anyio
async def test_get_prompt_not_found(client):
    response = await client.get("/api/v1/prompts/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_prompt(client):
    create = await client.post(
        "/api/v1/prompts", json={"name": "To Delete", "content": "delete me"}
    )
    prompt_id = create.json()["id"]

    delete = await client.delete(f"/api/v1/prompts/{prompt_id}")
    assert delete.status_code == 204

    get = await client.get(f"/api/v1/prompts/{prompt_id}")
    assert get.status_code == 404
