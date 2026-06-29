from fastapi import status

from tests.conftest import register_and_login


def test_register_returns_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "password123"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["id"] == 1
    assert body["email"] == "new@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email_rejected(client):
    payload = {"email": "dupe@example.com", "password": "password123"}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == status.HTTP_201_CREATED

    second = client.post("/auth/register", json=payload)
    assert second.status_code == status.HTTP_409_CONFLICT


def test_register_invalid_email_rejected(client):
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "password123"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_login_success_returns_token(client):
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "password123"},
    )

    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "password123"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password_rejected(client):
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "password123"},
    )

    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "wrong"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_unknown_user_rejected(client):
    response = client.post(
        "/auth/login",
        data={"username": "ghost@example.com", "password": "password123"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_returns_current_user(client):
    token = register_and_login(client, "me@example.com", "password123")

    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == "me@example.com"


def test_me_requires_token(client):
    response = client.get("/auth/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_invalid_token_rejected(client):
    response = client.get(
        "/tasks", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_tasks_are_isolated_per_user(client):
    token_a = register_and_login(client, "alice@example.com", "password123")
    token_b = register_and_login(client, "bob@example.com", "password123")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    created = client.post(
        "/tasks", json={"title": "Alice task"}, headers=headers_a
    ).json()

    # Bob cannot see Alice's task in his list...
    bob_list = client.get("/tasks", headers=headers_b)
    assert bob_list.json() == []

    # ...nor fetch, update, or delete it (404 hides existence).
    assert (
        client.get(f"/tasks/{created['id']}", headers=headers_b).status_code
        == status.HTTP_404_NOT_FOUND
    )
    assert (
        client.put(
            f"/tasks/{created['id']}",
            json={"title": "Hacked", "completed": True},
            headers=headers_b,
        ).status_code
        == status.HTTP_404_NOT_FOUND
    )
    assert (
        client.delete(f"/tasks/{created['id']}", headers=headers_b).status_code
        == status.HTTP_404_NOT_FOUND
    )

    # Alice still sees her own task.
    alice_list = client.get("/tasks", headers=headers_a)
    assert [t["title"] for t in alice_list.json()] == ["Alice task"]
