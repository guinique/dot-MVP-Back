def test_list_tutors_requires_admin(client, user_headers):
    response = client.get("/api/v1/tutors", headers=user_headers)
    assert response.status_code == 403


def test_create_and_get_tutor(client, admin_headers):
    create = client.post(
        "/api/v1/tutors",
        headers=admin_headers,
        json={
            "title": "Math Tutor",
            "description": "Algebra helper",
            "system_instructions": "Explain math step by step.",
            "source_urls": ["https://example.com/math.txt"],
        },
    )
    assert create.status_code == 201
    tutor_id = create.json()["id"]

    get_resp = client.get(f"/api/v1/tutors/{tutor_id}", headers=admin_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Math Tutor"


def test_update_tutor(client, admin_headers, sample_tutor):
    response = client.patch(
        f"/api/v1/tutors/{sample_tutor.id}",
        headers=admin_headers,
        json={"description": "Updated description"},
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description"


def test_deactivate_tutor(client, admin_headers, sample_tutor):
    response = client.post(
        f"/api/v1/tutors/{sample_tutor.id}/deactivate",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "inactive"


def test_delete_tutor(client, admin_headers, sample_tutor):
    tutor_id = sample_tutor.id
    response = client.delete(f"/api/v1/tutors/{tutor_id}", headers=admin_headers)
    assert response.status_code == 204

    get_resp = client.get(f"/api/v1/tutors/{tutor_id}", headers=admin_headers)
    assert get_resp.status_code == 404


def test_delete_tutor_with_chat_history(client, admin_headers, embed_headers, sample_tutor, db):
    from app.models.tutor import ChatMessage, ChatSession

    client.post(
        f"/api/v1/chat/tutors/{sample_tutor.id}/messages",
        headers=embed_headers,
        json={"message": "Hello"},
    )

    response = client.delete(f"/api/v1/tutors/{sample_tutor.id}", headers=admin_headers)
    assert response.status_code == 204

    assert db.query(ChatMessage).count() == 0
    assert db.query(ChatSession).count() == 0
