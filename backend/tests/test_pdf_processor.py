from pathlib import Path

from app.services.pdf_processor import extract_text_with_ocr, split_text_into_sections
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


def test_heading_detection_accepts_common_variants() -> None:
    text = "\n".join(
        [
            "Abstract:",
            "This paper describes a system.",
            "1 Introduction",
            "Motivation goes here.",
            "IV. Results",
            "The numbers look good.",
            "Conclusion.",
            "Closing remarks.",
        ]
    )

    sections = split_text_into_sections(text)
    section_types = [section["section_type"] for section in sections]

    assert section_types == ["abstract", "introduction", "results", "conclusion"]
