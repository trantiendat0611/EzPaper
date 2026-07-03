from fastapi.testclient import TestClient

from tests.conftest import pdf_bytes_with_text


def _upload_paper(client: TestClient, auth_headers: dict[str, str]) -> int:
    pdf_bytes = pdf_bytes_with_text(
        [
            "Abstract",
            "This paper introduces a caching system that speeds up database queries.",
            "Method",
            "The caching layer stores frequent query results in memory.",
        ]
    )
    upload = client.post(
        "/papers/upload",
        headers=auth_headers,
        files={"file": ("qa.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 201
    return upload.json()["id"]


def test_ask_question_persists_and_returns_answer(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    paper_id = _upload_paper(client, auth_headers)

    ask = client.post(
        f"/papers/{paper_id}/ask",
        headers=auth_headers,
        json={"question": "What does the caching system do?"},
    )
    assert ask.status_code == 201
    body = ask.json()
    assert body["question"] == "What does the caching system do?"
    assert body["answer"]
    assert body["provider"] == "local"

    history = client.get(f"/papers/{paper_id}/questions", headers=auth_headers)
    assert history.status_code == 200
    items = history.json()
    assert len(items) == 1
    assert items[0]["answer"] == body["answer"]


def test_ask_question_rejects_empty(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    paper_id = _upload_paper(client, auth_headers)

    ask = client.post(
        f"/papers/{paper_id}/ask",
        headers=auth_headers,
        json={"question": ""},
    )
    assert ask.status_code == 422


def test_ask_question_requires_ownership(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    paper_id = _upload_paper(client, auth_headers)

    client.post(
        "/auth/register",
        json={"email": "intruder@example.com", "password": "secret123"},
    )
    login = client.post(
        "/auth/login",
        json={"email": "intruder@example.com", "password": "secret123"},
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    ask = client.post(
        f"/papers/{paper_id}/ask",
        headers=other_headers,
        json={"question": "Anything?"},
    )
    assert ask.status_code == 404

    history = client.get(f"/papers/{paper_id}/questions", headers=other_headers)
    assert history.status_code == 404
