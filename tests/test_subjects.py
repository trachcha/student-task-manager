from fastapi import status

from tests.conftest import register_and_login


def _auth_headers(client, username: str) -> dict:
    token = register_and_login(client, username, "password123")
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
    headers_a = _auth_headers(client, "alice")
    headers_b = _auth_headers(client, "bob")

    first = client.post("/subjects", json={"name": "Math"}, headers=headers_a)
    second = client.post("/subjects", json={"name": "Math"}, headers=headers_b)

    assert first.status_code == status.HTTP_201_CREATED
    assert second.status_code == status.HTTP_201_CREATED


def test_subjects_require_authentication(client):
    response = client.get("/subjects")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_subjects_are_isolated_per_user(client):
    headers_a = _auth_headers(client, "alice")
    headers_b = _auth_headers(client, "bob")

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


def test_reorder_subjects_persists_order(auth_client):
    math = auth_client.post("/subjects", json={"name": "Math"}).json()
    history = auth_client.post("/subjects", json={"name": "History"}).json()

    response = auth_client.put(
        "/subjects/reorder",
        json={"subject_ids": [history["id"], 0, math["id"]]},
    )

    assert response.status_code == status.HTTP_200_OK
    names = [s["name"] for s in response.json()]
    assert names == ["History", "Math"]

    me = auth_client.get("/auth/me").json()
    assert me["unsorted_position"] == 1


def test_reorder_subjects_rejects_invalid_order(auth_client):
    math = auth_client.post("/subjects", json={"name": "Math"}).json()
    auth_client.post("/subjects", json={"name": "History"})

    response = auth_client.put(
        "/subjects/reorder",
        json={"subject_ids": [math["id"], 0]},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid subject order"}


def test_reorder_subjects_requires_unsorted_once(auth_client):
    math = auth_client.post("/subjects", json={"name": "Math"}).json()

    response = auth_client.put(
        "/subjects/reorder",
        json={"subject_ids": [math["id"]]},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_new_subject_appends_at_end(auth_client):
    math = auth_client.post("/subjects", json={"name": "Math"}).json()
    auth_client.put("/subjects/reorder", json={"subject_ids": [0, math["id"]]})

    history = auth_client.post("/subjects", json={"name": "History"}).json()

    names = [s["name"] for s in auth_client.get("/subjects").json()]
    assert names == ["Math", "History"]
    assert history["id"] > math["id"]
