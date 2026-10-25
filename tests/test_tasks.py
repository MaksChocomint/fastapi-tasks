from httpx import AsyncClient


async def test_create_task(client: AsyncClient, user: dict) -> None:
    response = await client.post("/tasks", json={"title": "Сделать ПЗ3", "owner_id": user["id"]})

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Сделать ПЗ3"
    assert data["description"] is None
    assert data["done"] is False
    assert data["owner_id"] == user["id"]


async def test_create_task_missing_owner(client: AsyncClient) -> None:
    response = await client.post("/tasks", json={"title": "Задача", "owner_id": 999})

    assert response.status_code == 404


async def test_create_task_empty_title(client: AsyncClient, user: dict) -> None:
    response = await client.post("/tasks", json={"title": "", "owner_id": user["id"]})

    assert response.status_code == 422


async def test_filter_done_and_pagination(client: AsyncClient, user: dict) -> None:
    for i in range(5):
        await client.post(
            "/tasks", json={"title": f"Задача {i}", "done": i % 2 == 0, "owner_id": user["id"]}
        )

    done = await client.get("/tasks", params={"done": True})
    assert done.status_code == 200
    assert [t["title"] for t in done.json()] == ["Задача 0", "Задача 2", "Задача 4"]

    page = await client.get("/tasks", params={"limit": 2, "offset": 1})
    assert page.status_code == 200
    assert [t["title"] for t in page.json()] == ["Задача 1", "Задача 2"]

    too_big = await client.get("/tasks", params={"limit": 101})
    assert too_big.status_code == 422


async def test_patch_changes_only_given_fields(client: AsyncClient, user: dict) -> None:
    created = await client.post(
        "/tasks",
        json={"title": "Старое название", "description": "Описание", "owner_id": user["id"]},
    )
    task_id = created.json()["id"]

    response = await client.patch(f"/tasks/{task_id}", json={"done": True})

    assert response.status_code == 200
    data = response.json()
    assert data["done"] is True
    assert data["title"] == "Старое название"
    assert data["description"] == "Описание"


async def test_delete_then_get_returns_404(client: AsyncClient, user: dict) -> None:
    created = await client.post("/tasks", json={"title": "Удалить", "owner_id": user["id"]})
    task_id = created.json()["id"]

    delete = await client.delete(f"/tasks/{task_id}")
    assert delete.status_code == 204

    get = await client.get(f"/tasks/{task_id}")
    assert get.status_code == 404


async def test_process_time_header(client: AsyncClient) -> None:
    response = await client.get("/tasks")

    assert response.status_code == 200
    assert "X-Process-Time" in response.headers
    assert float(response.headers["X-Process-Time"]) >= 0
