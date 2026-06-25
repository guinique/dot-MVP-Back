def test_chat_requires_embed_token(client, sample_tutor):
    response = client.post(
        f"/api/v1/chat/tutors/{sample_tutor.id}/messages",
        json={"message": "Hello"},
    )
    assert response.status_code == 401


def test_chat_with_mock_agent(client, embed_headers, sample_tutor):
    response = client.post(
        f"/api/v1/chat/tutors/{sample_tutor.id}/messages",
        headers=embed_headers,
        json={"message": "What is a variable?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "[mock]" in data["reply"]
    assert "Python Tutor" in data["reply"]
    assert data["session_key"]


def test_chat_session_continuity(client, embed_headers, sample_tutor, db):
    first = client.post(
        f"/api/v1/chat/tutors/{sample_tutor.id}/messages",
        headers=embed_headers,
        json={"message": "First message"},
    )
    session_key = first.json()["session_key"]

    second = client.post(
        f"/api/v1/chat/tutors/{sample_tutor.id}/messages",
        headers=embed_headers,
        json={"message": "Second message", "session_key": session_key},
    )
    assert second.status_code == 200
    assert second.json()["session_key"] == session_key

    from app.models.tutor import ChatMessage

    messages = db.query(ChatMessage).all()
    assert len(messages) == 4


def test_create_chat_session(client, embed_headers, sample_tutor):
    response = client.post(
        "/api/v1/chat/sessions",
        headers=embed_headers,
        json={"tutor_id": sample_tutor.id},
    )
    assert response.status_code == 201
    assert response.json()["tutor_id"] == sample_tutor.id


def test_chat_inactive_tutor_returns_404(client, embed_headers, admin_headers, sample_tutor):
    client.post(f"/api/v1/tutors/{sample_tutor.id}/deactivate", headers=admin_headers)
    response = client.post(
        f"/api/v1/chat/tutors/{sample_tutor.id}/messages",
        headers=embed_headers,
        json={"message": "Hello"},
    )
    assert response.status_code == 404


def test_get_session_messages(client, embed_headers, sample_tutor):
    post = client.post(
        f"/api/v1/chat/tutors/{sample_tutor.id}/messages",
        headers=embed_headers,
        json={"message": "Hello there"},
    )
    session_key = post.json()["session_key"]

    response = client.get(
        f"/api/v1/chat/tutors/{sample_tutor.id}/sessions/{session_key}/messages",
        headers=embed_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_key"] == session_key
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "Hello there"
    assert data["messages"][1]["role"] == "assistant"


def test_get_session_messages_not_found(client, embed_headers, sample_tutor):
    response = client.get(
        f"/api/v1/chat/tutors/{sample_tutor.id}/sessions/invalid-key/messages",
        headers=embed_headers,
    )
    assert response.status_code == 404


def test_get_session_messages_requires_embed_token(client, sample_tutor):
    response = client.get(
        f"/api/v1/chat/tutors/{sample_tutor.id}/sessions/any-key/messages",
    )
    assert response.status_code == 401
