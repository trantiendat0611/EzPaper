import re
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models.paper import Paper, PaperSection

SECTION_ALIASES = {
    "abstract": "abstract",
    "introduction": "introduction",
    "background": "background",
    "related work": "related_work",
    "method": "method",
    "methods": "method",
    "methodology": "method",
    "approach": "method",
    "experiments": "experiments",
    "experiment": "experiments",
    "results": "results",
    "discussion": "discussion",
    "conclusion": "conclusion",
    "conclusions": "conclusion",
    "references": "references",
}

# Accepts optional numbering ("2", "3.1", "IV") and an optional trailing
# colon/period, e.g. "Abstract:", "1 Introduction", "IV. Results".
HEADING_PATTERN = re.compile(
    r"^\s*(?:(?:\d+(?:\.\d+)*|[IVXLC]+)\.?\s+)?("
    + "|".join(re.escape(heading) for heading in SECTION_ALIASES)
    + r")\s*[:.]?\s*$",
    re.IGNORECASE,
)

# Below this length the pypdf output is treated as a likely image-only (scanned)
# PDF, and OCR is attempted as a fallback.
OCR_MIN_TEXT_LENGTH = 200


def extract_text_from_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    page_texts: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            page_texts.append(text.strip())

    return "\n\n".join(page_texts).strip()


def extract_text_with_ocr(file_path: Path) -> str:
    """OCR a scanned (image-only) PDF.

    Requires the pytesseract/pdf2image packages plus the Tesseract OCR and
    Poppler system binaries. Returns an empty string if any of those are
    missing so the caller can degrade gracefully.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        return ""

    try:
        images = convert_from_path(str(file_path))
    except Exception:
        return ""

    page_texts: list[str] = []
    for image in images:
        try:
            text = pytesseract.image_to_string(image)
        except Exception:
            return ""
        if text.strip():
            page_texts.append(text.strip())

    return "\n\n".join(page_texts).strip()


def split_text_into_sections(text: str) -> list[dict[str, str | int]]:
    lines = [line.strip() for line in text.splitlines()]
    sections: list[dict[str, str | int]] = []
    current_title = "Full Text"
    current_type = "full_text"
    current_lines: list[str] = []

    def flush_section() -> None:
        raw_text = "\n".join(line for line in current_lines if line).strip()
        if raw_text:
            sections.append(
                {
                    "title": current_title,
                    "section_type": current_type,
                    "order_index": len(sections),
                    "raw_text": raw_text,
                }
            )

    for line in lines:
        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            flush_section()
            current_title = heading_match.group(1).title()
            current_type = SECTION_ALIASES[heading_match.group(1).lower()]
            current_lines = []
            continue

        current_lines.append(line)

    flush_section()

    if not sections and text.strip():
        sections.append(
            {
                "title": "Full Text",
                "section_type": "full_text",
                "order_index": 0,
                "raw_text": text.strip(),
            }
        )

    return sections


def process_uploaded_pdf(db: Session, paper: Paper, file_path: Path) -> Paper:
    paper.status = "processing"
    db.commit()
    db.refresh(paper)

    try:
        extracted_text = extract_text_from_pdf(file_path)
        if len(extracted_text) < OCR_MIN_TEXT_LENGTH:
            ocr_text = extract_text_with_ocr(file_path)
            if len(ocr_text) > len(extracted_text):
                extracted_text = ocr_text

        if not extracted_text:
            paper.status = "failed"
            db.commit()
            db.refresh(paper)
            return paper

        sections = split_text_into_sections(extracted_text)
        for section in sections:
            db.add(
                PaperSection(
                    paper_id=paper.id,
                    title=str(section["title"])[:255],
                    section_type=str(section["section_type"])[:100],
                    order_index=int(section["order_index"]),
                    raw_text=str(section["raw_text"]),
                )
            )

        abstract = next(
            (section["raw_text"] for section in sections if section["section_type"] == "abstract"),
            None,
        )
        if abstract:
            paper.abstract = str(abstract)

        paper.status = "completed"
        db.commit()
        db.refresh(paper)
        return paper
    except Exception:
        paper.status = "failed"
        db.commit()
        db.refresh(paper)
        return paper
