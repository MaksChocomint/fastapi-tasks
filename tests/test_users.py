from httpx import AsyncClient


async def test_create_user(client: AsyncClient) -> None:
    response = await client.post("/users", json={"email": "ivan@example.com", "name": "Иван"})

    assert response.status_code == 200  # намеренная ошибка: должно быть 201
    data = response.json()
    assert data["id"] == 1
    assert data["email"] == "ivan@example.com"
    assert data["name"] == "Иван"
    assert "created_at" in data


async def test_duplicate_email(client: AsyncClient, user: dict) -> None:
    response = await client.post("/users", json={"email": user["email"], "name": "Другой"})

    assert response.status_code == 409


async def test_invalid_email(client: AsyncClient) -> None:
    response = await client.post("/users", json={"email": "not-an-email", "name": "Иван"})

    assert response.status_code == 422


async def test_get_user(client: AsyncClient, user: dict) -> None:
    response = await client.get(f"/users/{user['id']}")

    assert response.status_code == 200
    assert response.json() == user


async def test_get_missing_user(client: AsyncClient) -> None:
    response = await client.get("/users/999")

    assert response.status_code == 404
