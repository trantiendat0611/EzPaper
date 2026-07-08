from pathlib import Path

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.paper import Paper, PaperSection
from app.services.pdf_processor import process_uploaded_pdf
from app.services.section_analyzer import analyze_paper_sections, analyze_section


@celery_app.task(name="app.tasks.process_pdf_task")
def process_pdf_task(paper_id: int, file_path: str) -> None:
    db = SessionLocal()
    try:
        paper = db.get(Paper, paper_id)
        if paper is None:
            return
        process_uploaded_pdf(db, paper, Path(file_path))
    finally:
        db.close()


@celery_app.task(name="app.tasks.analyze_paper_task")
def analyze_paper_task(paper_id: int) -> None:
    db = SessionLocal()
    try:
        paper = db.get(Paper, paper_id)
        if paper is None:
            return
        try:
            analyze_paper_sections(db, paper)
        except Exception:
            # Never leave the paper stuck in "analyzing"; the user can retry.
            db.rollback()
            paper.status = "failed"
            db.commit()
            raise
    finally:
        db.close()


@celery_app.task(name="app.tasks.analyze_section_task")
def analyze_section_task(section_id: int) -> None:
    db = SessionLocal()
    try:
        section = db.get(PaperSection, section_id)
        if section is None:
            return
        paper = section.paper
        try:
            analyze_section(section)
            paper.status = "analyzed"
            db.commit()
        except Exception:
            db.rollback()
            paper.status = "failed"
            db.commit()
            raise
    finally:
        db.close()
