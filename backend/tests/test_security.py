from fastapi.testclient import TestClient

from app.core.limiter import limiter


def test_upload_rejects_file_with_invalid_pdf_content(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    fake_pdf = b"not actually a pdf file"

    response = client.post(
        "/papers/upload",
        headers=auth_headers,
        files={"file": ("fake.pdf", fake_pdf, "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File content is not a valid PDF"


def test_login_is_rate_limited(client: TestClient, registered_user: dict[str, str]) -> None:
    limiter.enabled = True
    limiter.reset()

    try:
        payload = {"email": registered_user["email"], "password": "wrong-password"}

        for _ in range(5):
            response = client.post("/auth/login", json=payload)
            assert response.status_code == 401

        limited_response = client.post("/auth/login", json=payload)
        assert limited_response.status_code == 429
    finally:
        limiter.reset()
        limiter.enabled = False


def test_register_is_rate_limited(client: TestClient) -> None:
    limiter.enabled = True
    limiter.reset()

    try:
        for index in range(5):
            response = client.post(
                "/auth/register",
                json={"email": f"user{index}@example.com", "password": "secret123"},
            )
            assert response.status_code == 201

        limited_response = client.post(
            "/auth/register",
            json={"email": "user-final@example.com", "password": "secret123"},
        )
        assert limited_response.status_code == 429
    finally:
        limiter.reset()
        limiter.enabled = False
