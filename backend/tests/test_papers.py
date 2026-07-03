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


def test_scanned_pdf_falls_back_to_ocr(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch,
) -> None:
    # Simulate a scanned PDF: pypdf finds no text, OCR recovers it.
    monkeypatch.setattr(
        "app.services.pdf_processor.extract_text_from_pdf",
        lambda file_path: "",
    )
    monkeypatch.setattr(
        "app.services.pdf_processor.extract_text_with_ocr",
        lambda file_path: "Abstract\nThis scanned paper was recovered via OCR fallback.",
    )

    pdf_bytes = pdf_bytes_with_text(["placeholder"])
    upload = client.post(
        "/papers/upload",
        headers=auth_headers,
        files={"file": ("scanned.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 201
    paper_id = upload.json()["id"]

    detail = client.get(f"/papers/{paper_id}", headers=auth_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "completed"
    assert body["abstract"] == "This scanned paper was recovered via OCR fallback."
    assert any("OCR fallback" in section["raw_text"] for section in body["sections"])


def _upload_named_paper(client: TestClient, auth_headers: dict[str, str], name: str) -> int:
    pdf_bytes = pdf_bytes_with_text(["Abstract", f"Content for {name}."])
    upload = client.post(
        "/papers/upload",
        headers=auth_headers,
        files={"file": (f"{name}.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 201
    return upload.json()["id"]


def test_list_papers_pagination_and_search(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    for name in ["alpha", "beta", "gamma"]:
        _upload_named_paper(client, auth_headers, name)

    first_page = client.get("/papers?page=1&page_size=2", headers=auth_headers)
    assert first_page.status_code == 200
    body = first_page.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2

    second_page = client.get("/papers?page=2&page_size=2", headers=auth_headers)
    assert len(second_page.json()["items"]) == 1

    search = client.get("/papers?search=alpha", headers=auth_headers)
    search_body = search.json()
    assert search_body["total"] == 1
    assert search_body["items"][0]["title"] == "alpha"


def test_paper_stats(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    for name in ["one", "two"]:
        _upload_named_paper(client, auth_headers, name)

    stats = client.get("/papers/stats", headers=auth_headers)
    assert stats.status_code == 200
    body = stats.json()
    assert body["total"] == 2
    assert body["extracted"] == 2
    assert body["analyzed"] == 0


def test_retry_single_section_analysis(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    pdf_bytes = pdf_bytes_with_text(["Abstract", "A short abstract for retry testing."])
    upload = client.post(
        "/papers/upload",
        headers=auth_headers,
        files={"file": ("retry.pdf", pdf_bytes, "application/pdf")},
    )
    paper_id = upload.json()["id"]

    detail = client.get(f"/papers/{paper_id}", headers=auth_headers)
    section_id = detail.json()["sections"][0]["id"]
    assert detail.json()["sections"][0]["summary_vi"] is None

    retry = client.post(
        f"/papers/{paper_id}/sections/{section_id}/analyze",
        headers=auth_headers,
    )
    assert retry.status_code == 200

    refreshed = client.get(f"/papers/{paper_id}", headers=auth_headers)
    target = next(s for s in refreshed.json()["sections"] if s["id"] == section_id)
    assert target["summary_vi"]
    assert target["explanation_vi"]

    missing = client.post(
        f"/papers/{paper_id}/sections/999999/analyze",
        headers=auth_headers,
    )
    assert missing.status_code == 404
