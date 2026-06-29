from fastapi import status

from tests.conftest import register_and_login


def _create_task(client, title: str = "Study SQL") -> dict:
    response = client.post("/tasks", json={"title": title})
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def test_health_check(client):
    response = client.get("/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "StudentTask API is running"}


def test_create_task(auth_client):
    response = auth_client.post("/tasks", json={"title": "Study SQL"})

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Study SQL"
    assert body["completed"] is False


def test_create_task_requires_title(auth_client):
    response = auth_client.post("/tasks", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_all_tasks_empty(auth_client):
    response = auth_client.get("/tasks")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_all_tasks_returns_created(auth_client):
    _create_task(auth_client, "First")
    _create_task(auth_client, "Second")

    response = auth_client.get("/tasks")

    assert response.status_code == status.HTTP_200_OK
    titles = [task["title"] for task in response.json()]
    assert titles == ["First", "Second"]


def test_get_task_by_id(auth_client):
    created = _create_task(auth_client)

    response = auth_client.get(f"/tasks/{created['id']}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == created


def test_get_task_not_found(auth_client):
    response = auth_client.get("/tasks/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Task not found"}


def test_update_task(auth_client):
    created = _create_task(auth_client)

    response = auth_client.put(
        f"/tasks/{created['id']}",
        json={"title": "Study SQL well", "completed": True},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["title"] == "Study SQL well"
    assert body["completed"] is True


def test_update_task_persists(auth_client):
    created = _create_task(auth_client)

    auth_client.put(
        f"/tasks/{created['id']}",
        json={"title": "Updated", "completed": True},
    )
    response = auth_client.get(f"/tasks/{created['id']}")

    body = response.json()
    assert body["title"] == "Updated"
    assert body["completed"] is True


def test_update_task_not_found(auth_client):
    response = auth_client.put(
        "/tasks/999",
        json={"title": "Nope", "completed": True},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Task not found"}


def test_delete_task(auth_client):
    created = _create_task(auth_client)

    response = auth_client.delete(f"/tasks/{created['id']}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Task deleted successfully"}

    follow_up = auth_client.get(f"/tasks/{created['id']}")
    assert follow_up.status_code == status.HTTP_404_NOT_FOUND


def test_delete_task_not_found(auth_client):
    response = auth_client.delete("/tasks/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Task not found"}


def test_database_isolated_between_tests(auth_client):
    """Each test starts from an empty database (fixture isolation)."""
    response = auth_client.get("/tasks")

    assert response.json() == []


def test_tasks_require_authentication(client):
    """Without a bearer token the task endpoints reject the request."""
    response = client.get("/tasks")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_task_defaults_to_no_subject(auth_client):
    created = _create_task(auth_client)

    assert created["subject_id"] is None


def test_create_task_with_subject(auth_client):
    subject = auth_client.post("/subjects", json={"name": "Math"}).json()

    response = auth_client.post(
        "/tasks", json={"title": "Homework", "subject_id": subject["id"]}
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["subject_id"] == subject["id"]


def test_create_task_with_unknown_subject_rejected(auth_client):
    response = auth_client.post(
        "/tasks", json={"title": "Homework", "subject_id": 999}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Subject not found"}


def test_assigning_another_users_subject_rejected(client):
    token_a = register_and_login(client, "alice@example.com", "password123")
    token_b = register_and_login(client, "bob@example.com", "password123")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    subject = client.post(
        "/subjects", json={"name": "Math"}, headers=headers_a
    ).json()

    response = client.post(
        "/tasks",
        json={"title": "Homework", "subject_id": subject["id"]},
        headers=headers_b,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_task_assigns_and_clears_subject(auth_client):
    subject = auth_client.post("/subjects", json={"name": "Math"}).json()
    created = _create_task(auth_client)

    assigned = auth_client.put(
        f"/tasks/{created['id']}",
        json={"title": created["title"], "completed": False, "subject_id": subject["id"]},
    )
    assert assigned.json()["subject_id"] == subject["id"]

    cleared = auth_client.put(
        f"/tasks/{created['id']}",
        json={"title": created["title"], "completed": False},
    )
    assert cleared.json()["subject_id"] is None


def test_filter_tasks_by_subject(auth_client):
    math = auth_client.post("/subjects", json={"name": "Math"}).json()
    history = auth_client.post("/subjects", json={"name": "History"}).json()

    auth_client.post("/tasks", json={"title": "Algebra", "subject_id": math["id"]})
    auth_client.post("/tasks", json={"title": "WW2", "subject_id": history["id"]})
    auth_client.post("/tasks", json={"title": "Unfiled"})

    response = auth_client.get(f"/tasks?subject_id={math['id']}")

    assert response.status_code == status.HTTP_200_OK
    titles = [t["title"] for t in response.json()]
    assert titles == ["Algebra"]
