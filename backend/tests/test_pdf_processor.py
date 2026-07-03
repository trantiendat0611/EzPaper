from pathlib import Path

from app.services.pdf_processor import extract_text_with_ocr
from tests.conftest import pdf_bytes_with_text


def test_ocr_returns_empty_when_binaries_missing() -> None:
    # Tesseract/Poppler are not installed in the test environment, so OCR must
    # degrade gracefully to an empty string instead of raising.
    upload_dir = Path("storage") / "test-uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    pdf_file = upload_dir / "ocr-degradation-sample.pdf"
    pdf_file.write_bytes(pdf_bytes_with_text(["Some text"]))

    try:
        assert extract_text_with_ocr(pdf_file) == ""
    finally:
        pdf_file.unlink(missing_ok=True)
