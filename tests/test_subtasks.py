from fastapi import status
from sqlalchemy import text

from tests.conftest import register_and_login


def _create_task(client, title: str = "Project") -> dict:
    response = client.post("/tasks", json={"title": title})
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def _create_subtask(client, task_id: int, title: str = "Step 1") -> dict:
    response = client.post(f"/tasks/{task_id}/subtasks", json={"title": title})
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def test_create_subtask(auth_client):
    task = _create_task(auth_client)

    response = auth_client.post(
        f"/tasks/{task['id']}/subtasks", json={"title": "Step 1"}
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Step 1"
    assert body["completed"] is False
    assert body["task_id"] == task["id"]


def test_create_subtask_requires_title(auth_client):
    task = _create_task(auth_client)

    response = auth_client.post(f"/tasks/{task['id']}/subtasks", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_subtask_unknown_task(auth_client):
    response = auth_client.post("/tasks/999/subtasks", json={"title": "Step 1"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Task not found"}


def test_list_subtasks(auth_client):
    task = _create_task(auth_client)
    _create_subtask(auth_client, task["id"], "First")
    _create_subtask(auth_client, task["id"], "Second")

    response = auth_client.get(f"/tasks/{task['id']}/subtasks")

    assert response.status_code == status.HTTP_200_OK
    titles = [s["title"] for s in response.json()]
    assert titles == ["First", "Second"]


def test_get_subtask_by_id(auth_client):
    task = _create_task(auth_client)
    created = _create_subtask(auth_client, task["id"])

    response = auth_client.get(f"/tasks/{task['id']}/subtasks/{created['id']}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == created


def test_get_subtask_not_found(auth_client):
    task = _create_task(auth_client)

    response = auth_client.get(f"/tasks/{task['id']}/subtasks/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Subtask not found"}


def test_update_subtask(auth_client):
    task = _create_task(auth_client)
    created = _create_subtask(auth_client, task["id"])

    response = auth_client.put(
        f"/tasks/{task['id']}/subtasks/{created['id']}",
        json={"title": "Done step", "completed": True},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["title"] == "Done step"
    assert body["completed"] is True


def test_update_subtask_not_found(auth_client):
    task = _create_task(auth_client)

    response = auth_client.put(
        f"/tasks/{task['id']}/subtasks/999",
        json={"title": "Nope", "completed": True},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_subtask(auth_client):
    task = _create_task(auth_client)
    created = _create_subtask(auth_client, task["id"])

    response = auth_client.delete(f"/tasks/{task['id']}/subtasks/{created['id']}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Subtask deleted successfully"}

    follow_up = auth_client.get(f"/tasks/{task['id']}/subtasks/{created['id']}")
    assert follow_up.status_code == status.HTTP_404_NOT_FOUND


def test_delete_subtask_not_found(auth_client):
    task = _create_task(auth_client)

    response = auth_client.delete(f"/tasks/{task['id']}/subtasks/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_completing_subtask_does_not_change_task(auth_client):
    task = _create_task(auth_client)
    subtask = _create_subtask(auth_client, task["id"])

    auth_client.put(
        f"/tasks/{task['id']}/subtasks/{subtask['id']}",
        json={"title": subtask["title"], "completed": True},
    )

    refreshed_task = auth_client.get(f"/tasks/{task['id']}").json()
    assert refreshed_task["completed"] is False


def test_subtasks_require_authentication(client):
    response = client.get("/tasks/1/subtasks")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_subtasks_isolated_per_user(client):
    token_a = register_and_login(client, "alice@example.com", "password123")
    token_b = register_and_login(client, "bob@example.com", "password123")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    task = client.post("/tasks", json={"title": "Alice task"}, headers=headers_a).json()
    subtask = client.post(
        f"/tasks/{task['id']}/subtasks", json={"title": "Step"}, headers=headers_a
    ).json()

    # Bob cannot reach Alice's task's subtasks (task ownership hides them).
    assert (
        client.get(f"/tasks/{task['id']}/subtasks", headers=headers_b).status_code
        == status.HTTP_404_NOT_FOUND
    )
    assert (
        client.get(
            f"/tasks/{task['id']}/subtasks/{subtask['id']}", headers=headers_b
        ).status_code
        == status.HTTP_404_NOT_FOUND
    )


def test_subtask_from_another_task_not_found(auth_client):
    task_one = _create_task(auth_client, "One")
    task_two = _create_task(auth_client, "Two")
    subtask = _create_subtask(auth_client, task_one["id"])

    # The subtask exists, but not under task_two.
    response = auth_client.get(f"/tasks/{task_two['id']}/subtasks/{subtask['id']}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_deleting_task_cascades_subtasks(auth_client):
    from app.database.database import engine

    task = _create_task(auth_client)
    _create_subtask(auth_client, task["id"], "a")
    _create_subtask(auth_client, task["id"], "b")

    auth_client.delete(f"/tasks/{task['id']}")

    with engine.connect() as connection:
        remaining = connection.execute(
            text("SELECT count(*) FROM subtasks WHERE task_id = :tid"),
            {"tid": task["id"]},
        ).scalar()
    assert remaining == 0
