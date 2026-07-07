from fastapi import status

from tests.conftest import register_and_login


def _create_task(client, title: str = "Study SQL", **extra) -> dict:
    payload = {"title": title, **extra}
    response = client.post("/tasks", json=payload)
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
    assert body["description"] is None
    assert body["priority"] == "medium"
    assert body["due_date"] is None


def test_create_task_requires_title(auth_client):
    response = auth_client.post("/tasks", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_task_rejects_blank_title(auth_client):
    response = auth_client.post("/tasks", json={"title": "   "})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_task_rejects_title_over_200_characters(auth_client):
    response = auth_client.post("/tasks", json={"title": "a" * 201})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["detail"][0]["msg"] == "Task titles must be under 200 characters"


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
        json={
            "title": "Study SQL well",
            "description": None,
            "priority": "medium",
            "due_date": None,
            "completed": True,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["title"] == "Study SQL well"
    assert body["completed"] is True


def test_update_task_persists(auth_client):
    created = _create_task(auth_client)

    auth_client.put(
        f"/tasks/{created['id']}",
        json={
            "title": "Updated",
            "description": None,
            "priority": "medium",
            "due_date": None,
            "completed": True,
        },
    )
    response = auth_client.get(f"/tasks/{created['id']}")

    body = response.json()
    assert body["title"] == "Updated"
    assert body["completed"] is True


def test_update_task_not_found(auth_client):
    response = auth_client.put(
        "/tasks/999",
        json={
            "title": "Nope",
            "description": None,
            "priority": "medium",
            "due_date": None,
            "completed": True,
        },
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
    token_a = register_and_login(client, "alice", "password123")
    token_b = register_and_login(client, "bob", "password123")
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
        json={
            "title": created["title"],
            "description": None,
            "priority": "medium",
            "due_date": None,
            "completed": False,
            "subject_id": subject["id"],
        },
    )
    assert assigned.json()["subject_id"] == subject["id"]

    cleared = auth_client.put(
        f"/tasks/{created['id']}",
        json={
            "title": created["title"],
            "description": None,
            "priority": "medium",
            "due_date": None,
            "completed": False,
        },
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


def _complete(client, task: dict) -> None:
    client.put(
        f"/tasks/{task['id']}",
        json={
            "title": task["title"],
            "description": task.get("description"),
            "priority": task.get("priority", "medium"),
            "due_date": task.get("due_date"),
            "completed": True,
            "subject_id": task.get("subject_id"),
        },
    )


def test_filter_tasks_by_completed(auth_client):
    done = _create_task(auth_client, "Done")
    _create_task(auth_client, "Pending")
    _complete(auth_client, done)

    completed = auth_client.get("/tasks?completed=true")
    assert [t["title"] for t in completed.json()] == ["Done"]

    pending = auth_client.get("/tasks?completed=false")
    assert [t["title"] for t in pending.json()] == ["Pending"]


def test_search_tasks_case_insensitive_substring(auth_client):
    _create_task(auth_client, "Study SQL")
    _create_task(auth_client, "Buy milk")

    response = auth_client.get("/tasks?q=sql")

    assert response.status_code == status.HTTP_200_OK
    assert [t["title"] for t in response.json()] == ["Study SQL"]


def test_search_tasks_no_match_returns_empty(auth_client):
    _create_task(auth_client, "Study SQL")

    response = auth_client.get("/tasks?q=python")

    assert response.json() == []


def test_blank_search_is_ignored(auth_client):
    _create_task(auth_client, "First")
    _create_task(auth_client, "Second")

    response = auth_client.get("/tasks?q=%20")

    assert [t["title"] for t in response.json()] == ["First", "Second"]


def test_combined_filters_are_anded(auth_client):
    math = auth_client.post("/subjects", json={"name": "Math"}).json()
    keep = auth_client.post(
        "/tasks", json={"title": "Study algebra", "subject_id": math["id"]}
    ).json()
    # Same subject + matches q, but not completed -> excluded.
    auth_client.post("/tasks", json={"title": "Study geometry", "subject_id": math["id"]})
    # Completed + matches q, but different subject -> excluded.
    other = auth_client.post("/tasks", json={"title": "Study history"}).json()
    _complete(auth_client, keep)
    _complete(auth_client, other)

    response = auth_client.get(
        f"/tasks?completed=true&q=study&subject_id={math['id']}"
    )

    assert [t["title"] for t in response.json()] == ["Study algebra"]


def test_search_treats_wildcards_literally(auth_client):
    _create_task(auth_client, "50% done")
    _create_task(auth_client, "50 done")

    response = auth_client.get("/tasks?q=50%25")  # %25 is an encoded '%'

    assert [t["title"] for t in response.json()] == ["50% done"]


def test_invalid_completed_value_rejected(auth_client):
    response = auth_client.get("/tasks?completed=notabool")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_task_appends_to_end_of_active_list(auth_client):
    first = _create_task(auth_client, "First")
    second = _create_task(auth_client, "Second")

    assert first["position"] == 0
    assert second["position"] == 1

    active = auth_client.get("/tasks?completed=false").json()
    assert [task["title"] for task in active] == ["First", "Second"]


def test_reorder_tasks_persists_active_order(auth_client):
    first = _create_task(auth_client, "First")
    second = _create_task(auth_client, "Second")
    third = _create_task(auth_client, "Third")

    response = auth_client.put(
        "/tasks/reorder",
        json={"completed": False, "task_ids": [third["id"], first["id"], second["id"]]},
    )

    assert response.status_code == status.HTTP_200_OK
    assert [task["title"] for task in response.json()] == ["Third", "First", "Second"]

    active = auth_client.get("/tasks?completed=false").json()
    assert [task["title"] for task in active] == ["Third", "First", "Second"]


def test_reorder_rejects_partial_task_list(auth_client):
    first = _create_task(auth_client, "First")
    _create_task(auth_client, "Second")

    response = auth_client.put(
        "/tasks/reorder",
        json={"completed": False, "task_ids": [first["id"]]},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_completing_task_moves_it_to_end_of_completed_bucket(auth_client):
    first = _create_task(auth_client, "First")
    second = _create_task(auth_client, "Second")
    done = _create_task(auth_client, "Done")
    _complete(auth_client, done)

    _complete(auth_client, first)

    completed = auth_client.get("/tasks?completed=true").json()
    assert [task["title"] for task in completed] == ["Done", "First"]

    active = auth_client.get("/tasks?completed=false").json()
    assert [task["title"] for task in active] == ["Second"]
    assert completed[0]["position"] == 0
    assert completed[1]["position"] == 1


def test_create_task_with_description_priority_and_due_date(auth_client):
    response = auth_client.post(
        "/tasks",
        json={
            "title": "Essay draft",
            "description": "Write the introduction and outline.",
            "priority": "high",
            "due_date": "2026-08-15",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["description"] == "Write the introduction and outline."
    assert body["priority"] == "high"
    assert body["due_date"] == "2026-08-15"


def test_create_task_defaults_priority_to_medium(auth_client):
    created = _create_task(auth_client)

    assert created["priority"] == "medium"


def test_update_task_description_priority_and_due_date(auth_client):
    created = _create_task(auth_client)

    response = auth_client.put(
        f"/tasks/{created['id']}",
        json={
            "title": created["title"],
            "description": "Updated notes",
            "priority": "low",
            "due_date": "2026-09-01",
            "completed": False,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["description"] == "Updated notes"
    assert body["priority"] == "low"
    assert body["due_date"] == "2026-09-01"


def test_search_tasks_matches_description(auth_client):
    auth_client.post(
        "/tasks",
        json={
            "title": "Project",
            "description": "Include citations and bibliography",
        },
    )
    _create_task(auth_client, "Unrelated")

    response = auth_client.get("/tasks?q=bibliography")

    assert response.status_code == status.HTTP_200_OK
    assert [t["title"] for t in response.json()] == ["Project"]


def test_create_task_rejects_invalid_priority(auth_client):
    response = auth_client.post(
        "/tasks",
        json={"title": "Bad priority", "priority": "urgent"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
