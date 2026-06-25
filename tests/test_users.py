def test_list_users_requires_admin(client, user_headers):
    response = client.get("/api/v1/users", headers=user_headers)
    assert response.status_code == 403


def test_list_users_as_admin(client, admin_headers, regular_user):
    response = client.get("/api/v1/users", headers=admin_headers)
    assert response.status_code == 200
    emails = [u["email"] for u in response.json()]
    assert "admin@test.com" in emails
    assert regular_user.email in emails


def test_create_user_as_admin(client, admin_headers):
    response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "email": "new@test.com",
            "password": "newpass12",
            "full_name": "New User",
            "role": "user",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@test.com"
    assert data["role"] == "user"
    assert data["is_active"] is True


def test_create_user_duplicate_email(client, admin_headers, regular_user):
    response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "email": regular_user.email,
            "password": "another12",
        },
    )
    assert response.status_code == 409


def test_get_user_as_admin(client, admin_headers, regular_user):
    response = client.get(f"/api/v1/users/{regular_user.id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["email"] == regular_user.email


def test_get_user_not_found(client, admin_headers):
    response = client.get("/api/v1/users/9999", headers=admin_headers)
    assert response.status_code == 404


def test_update_user_as_admin(client, admin_headers, regular_user):
    response = client.patch(
        f"/api/v1/users/{regular_user.id}",
        headers=admin_headers,
        json={"full_name": "Updated Name", "is_active": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["is_active"] is False


def test_update_user_duplicate_email(client, admin_headers, admin_user, regular_user):
    response = client.patch(
        f"/api/v1/users/{regular_user.id}",
        headers=admin_headers,
        json={"email": admin_user.email},
    )
    assert response.status_code == 409


def test_delete_user_as_admin(client, admin_headers, db, regular_user):
    user_id = regular_user.id
    response = client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/users/{user_id}", headers=admin_headers)
    assert get_response.status_code == 404


def test_admin_cannot_delete_self(client, admin_headers, admin_user):
    response = client.delete(f"/api/v1/users/{admin_user.id}", headers=admin_headers)
    assert response.status_code == 400


def test_users_routes_require_auth(client):
    response = client.get("/api/v1/users")
    assert response.status_code == 401
