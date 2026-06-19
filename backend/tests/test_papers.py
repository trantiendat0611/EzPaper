from fastapi.testclient import TestClient

from tests.conftest import pdf_bytes_with_text


def test_paper_upload_extract_analyze_and_delete(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    pdf_bytes = pdf_bytes_with_text(
        [
            "Abstract",
            "EzPaper helps beginners understand scientific papers.",
            "Introduction",
            "Scientific papers are hard for beginners because they use technical language.",
            "Method",
            "The backend extracts text, detects headings, and stores structured sections.",
            "Conclusion",
            "This pipeline prepares EzPaper for AI-powered Vietnamese explanations.",
        ]
    )

    upload = client.post(
        "/papers/upload",
        headers=auth_headers,
        files={"file": ("ezpaper-sample.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 201
    uploaded = upload.json()
    assert uploaded["status"] == "completed"
    assert uploaded["abstract"] == "EzPaper helps beginners understand scientific papers."

    list_response = client.get("/papers", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()["items"]) == 1

    detail = client.get(f"/papers/{uploaded['id']}", headers=auth_headers)
    assert detail.status_code == 200
    detail_body = detail.json()
    assert len(detail_body["sections"]) == 4
    assert detail_body["sections"][0]["section_type"] == "abstract"
    assert detail_body["sections"][0]["summary_vi"] is None

    analysis = client.post(f"/papers/{uploaded['id']}/analyze", headers=auth_headers)
    assert analysis.status_code == 200
    analyzed = analysis.json()
    assert analyzed["status"] == "analyzed"
    assert analyzed["analysis_provider"] == "local"
    assert all(section["summary_vi"] for section in analyzed["sections"])
    assert all(section["explanation_vi"] for section in analyzed["sections"])

    delete_response = client.delete(f"/papers/{uploaded['id']}", headers=auth_headers)
    assert delete_response.status_code == 204

    missing = client.get(f"/papers/{uploaded['id']}", headers=auth_headers)
    assert missing.status_code == 404


def test_paper_requires_auth_and_pdf_file(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    unauthorized = client.get("/papers")
    assert unauthorized.status_code == 401

    invalid_upload = client.post(
        "/papers/upload",
        headers=auth_headers,
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )
    assert invalid_upload.status_code == 400


def test_user_cannot_read_another_users_paper(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    pdf_bytes = pdf_bytes_with_text(["Abstract", "Private paper content."])
    upload = client.post(
        "/papers/upload",
        headers=auth_headers,
        files={"file": ("private.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 201
    paper_id = upload.json()["id"]

    client.post(
        "/auth/register",
        json={
            "email": "other@example.com",
            "password": "secret123",
            "full_name": "Other User",
        },
    )
    login = client.post(
        "/auth/login",
        json={"email": "other@example.com", "password": "secret123"},
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    detail = client.get(f"/papers/{paper_id}", headers=other_headers)
    assert detail.status_code == 404

    delete_response = client.delete(f"/papers/{paper_id}", headers=other_headers)
    assert delete_response.status_code == 404
