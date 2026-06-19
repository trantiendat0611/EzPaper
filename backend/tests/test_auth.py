from fastapi.testclient import TestClient


def test_root_and_health(client: TestClient) -> None:
    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["docs"] == "/docs"

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    db_health = client.get("/health/db")
    assert db_health.status_code == 200
    assert db_health.json()["database"] == "connected"


def test_register_login_and_read_current_user(client: TestClient) -> None:
    register = client.post(
        "/auth/register",
        json={
            "email": "learner@example.com",
            "password": "secret123",
            "full_name": "Learner",
        },
    )
    assert register.status_code == 201
    assert register.json()["email"] == "learner@example.com"
    assert "hashed_password" not in register.json()

    duplicate = client.post(
        "/auth/register",
        json={
            "email": "learner@example.com",
            "password": "secret123",
            "full_name": "Learner",
        },
    )
    assert duplicate.status_code == 409

    bad_login = client.post(
        "/auth/login",
        json={"email": "learner@example.com", "password": "wrong-password"},
    )
    assert bad_login.status_code == 401

    login = client.post(
        "/auth/login",
        json={"email": "learner@example.com", "password": "secret123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    current_user = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert current_user.status_code == 200
    assert current_user.json()["email"] == "learner@example.com"


def test_swagger_token_login(client: TestClient, registered_user: dict[str, str]) -> None:
    response = client.post(
        "/auth/token",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
