from pathlib import Path
import re

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

HEADING_PATTERN = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*\.?\s+)?("
    + "|".join(re.escape(heading) for heading in SECTION_ALIASES)
    + r")\s*$",
    re.IGNORECASE,
)


def extract_text_from_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    page_texts: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
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
