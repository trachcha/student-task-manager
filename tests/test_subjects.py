from fastapi import status

from tests.conftest import register_and_login


def _auth_headers(client, email: str) -> dict:
    token = register_and_login(client, email, "password123")
    return {"Authorization": f"Bearer {token}"}


def test_create_subject(auth_client):
    response = auth_client.post("/subjects", json={"name": "Math"})

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == "Math"


def test_create_subject_requires_name(auth_client):
    response = auth_client.post("/subjects", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_subjects(auth_client):
    auth_client.post("/subjects", json={"name": "Math"})
    auth_client.post("/subjects", json={"name": "History"})

    response = auth_client.get("/subjects")

    assert response.status_code == status.HTTP_200_OK
    names = [s["name"] for s in response.json()]
    assert names == ["Math", "History"]


def test_get_subject_by_id(auth_client):
    created = auth_client.post("/subjects", json={"name": "Math"}).json()

    response = auth_client.get(f"/subjects/{created['id']}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == created


def test_get_subject_not_found(auth_client):
    response = auth_client.get("/subjects/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Subject not found"}


def test_update_subject(auth_client):
    created = auth_client.post("/subjects", json={"name": "Math"}).json()

    response = auth_client.put(
        f"/subjects/{created['id']}", json={"name": "Mathematics"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Mathematics"


def test_update_subject_not_found(auth_client):
    response = auth_client.put("/subjects/999", json={"name": "Nope"})

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_subject(auth_client):
    created = auth_client.post("/subjects", json={"name": "Math"}).json()

    response = auth_client.delete(f"/subjects/{created['id']}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Subject deleted successfully"}

    follow_up = auth_client.get(f"/subjects/{created['id']}")
    assert follow_up.status_code == status.HTTP_404_NOT_FOUND


def test_delete_subject_not_found(auth_client):
    response = auth_client.delete("/subjects/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_duplicate_subject_name_rejected(auth_client):
    auth_client.post("/subjects", json={"name": "Math"})

    response = auth_client.post("/subjects", json={"name": "Math"})

    assert response.status_code == status.HTTP_409_CONFLICT


def test_update_to_duplicate_name_rejected(auth_client):
    auth_client.post("/subjects", json={"name": "Math"})
    other = auth_client.post("/subjects", json={"name": "History"}).json()

    response = auth_client.put(f"/subjects/{other['id']}", json={"name": "Math"})

    assert response.status_code == status.HTTP_409_CONFLICT


def test_update_subject_same_name_allowed(auth_client):
    created = auth_client.post("/subjects", json={"name": "Math"}).json()

    response = auth_client.put(f"/subjects/{created['id']}", json={"name": "Math"})

    assert response.status_code == status.HTTP_200_OK


def test_same_name_allowed_for_different_users(client):
    headers_a = _auth_headers(client, "alice@example.com")
    headers_b = _auth_headers(client, "bob@example.com")

    first = client.post("/subjects", json={"name": "Math"}, headers=headers_a)
    second = client.post("/subjects", json={"name": "Math"}, headers=headers_b)

    assert first.status_code == status.HTTP_201_CREATED
    assert second.status_code == status.HTTP_201_CREATED


def test_subjects_require_authentication(client):
    response = client.get("/subjects")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_subjects_are_isolated_per_user(client):
    headers_a = _auth_headers(client, "alice@example.com")
    headers_b = _auth_headers(client, "bob@example.com")

    created = client.post(
        "/subjects", json={"name": "Math"}, headers=headers_a
    ).json()

    assert client.get("/subjects", headers=headers_b).json() == []
    assert (
        client.get(f"/subjects/{created['id']}", headers=headers_b).status_code
        == status.HTTP_404_NOT_FOUND
    )
    assert (
        client.put(
            f"/subjects/{created['id']}",
            json={"name": "Hacked"},
            headers=headers_b,
        ).status_code
        == status.HTTP_404_NOT_FOUND
    )
    assert (
        client.delete(f"/subjects/{created['id']}", headers=headers_b).status_code
        == status.HTTP_404_NOT_FOUND
    )


def test_deleting_subject_unassigns_tasks(auth_client):
    subject = auth_client.post("/subjects", json={"name": "Math"}).json()
    task = auth_client.post(
        "/tasks", json={"title": "Homework", "subject_id": subject["id"]}
    ).json()
    assert task["subject_id"] == subject["id"]

    auth_client.delete(f"/subjects/{subject['id']}")

    # Task survives but is unassigned.
    refreshed = auth_client.get(f"/tasks/{task['id']}")
    assert refreshed.status_code == status.HTTP_200_OK
    assert refreshed.json()["subject_id"] is None
