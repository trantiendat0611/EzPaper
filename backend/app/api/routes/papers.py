from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.limiter import limiter
from app.models.paper import Paper, PaperQuestion, PaperSection
from app.models.user import User
from app.schemas.paper import (
    PaperDetail,
    PaperList,
    PaperQuestionCreate,
    PaperQuestionRead,
    PaperRead,
    PaperStats,
)
from app.services.qa_service import answer_question
from app.tasks import analyze_paper_task, analyze_section_task, process_pdf_task

router = APIRouter(prefix="/papers", tags=["papers"])


def _get_upload_dir() -> Path:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


async def _validate_pdf(file: UploadFile) -> None:
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    if file.content_type not in {"application/pdf", "application/x-pdf", "application/octet-stream"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a PDF",
        )

    header = await file.read(5)
    await file.seek(0)
    if header != b"%PDF-":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content is not a valid PDF",
        )


@router.post("/upload", response_model=PaperRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def upload_paper(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Paper:
    await _validate_pdf(file)

    upload_dir = _get_upload_dir()
    original_filename = Path(file.filename or "paper.pdf").name
    stored_filename = f"{uuid4()}.pdf"
    destination = upload_dir / stored_filename

    total_size = 0
    with destination.open("wb") as output_file:
        while chunk := await file.read(1024 * 1024):
            total_size += len(chunk)
            if total_size > settings.max_upload_size_bytes:
                output_file.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"PDF must be {settings.max_upload_size_mb}MB or smaller",
                )
            output_file.write(chunk)

    title = Path(original_filename).stem or "Untitled Paper"
    paper = Paper(
        user_id=current_user.id,
        title=title,
        original_filename=original_filename,
        stored_filename=stored_filename,
        status="uploaded",
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    try:
        process_pdf_task.delay(paper.id, str(destination))
    except Exception as exc:
        paper.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Background processing is unavailable. Please try again later.",
        ) from exc

    db.refresh(paper)

    return paper


@router.get("", response_model=PaperList)
def list_papers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    search: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
) -> PaperList:
    base_query = select(Paper).where(Paper.user_id == current_user.id)
    if search:
        base_query = base_query.where(Paper.title.ilike(f"%{search}%"))
    if status_filter:
        base_query = base_query.where(Paper.status == status_filter)

    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    papers = db.scalars(
        base_query.order_by(Paper.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return PaperList(items=list(papers), total=total)


@router.get("/stats", response_model=PaperStats)
def paper_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaperStats:
    owned = select(func.count()).select_from(Paper).where(Paper.user_id == current_user.id)
    total = db.scalar(owned) or 0
    extracted = db.scalar(owned.where(Paper.status.in_(["completed", "analyzed"]))) or 0
    analyzed = db.scalar(owned.where(Paper.status == "analyzed")) or 0
    return PaperStats(total=total, extracted=extracted, analyzed=analyzed)


@router.get("/{paper_id}", response_model=PaperDetail)
def get_paper(
    paper_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Paper:
    paper = db.scalar(
        select(Paper)
        .options(selectinload(Paper.sections))
        .where(Paper.id == paper_id, Paper.user_id == current_user.id)
    )
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    return paper


@router.post("/{paper_id}/analyze", response_model=PaperDetail)
@limiter.limit("10/minute")
def analyze_paper(
    request: Request,
    paper_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Paper:
    paper = db.scalar(
        select(Paper)
        .options(selectinload(Paper.sections))
        .where(Paper.id == paper_id, Paper.user_id == current_user.id)
    )
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    if not paper.sections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paper has no extracted sections to analyze",
        )

    paper.status = "analyzing"
    db.commit()

    try:
        analyze_paper_task.delay(paper.id)
    except Exception as exc:
        db.rollback()
        paper.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analysis could not be started. Please try again later.",
        ) from exc

    db.refresh(paper)

    return paper


@router.post("/{paper_id}/sections/{section_id}/analyze", response_model=PaperDetail)
@limiter.limit("20/minute")
def analyze_single_section(
    request: Request,
    paper_id: int,
    section_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Paper:
    paper = db.scalar(
        select(Paper)
        .options(selectinload(Paper.sections))
        .where(Paper.id == paper_id, Paper.user_id == current_user.id)
    )
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    section = db.scalar(
        select(PaperSection).where(
            PaperSection.id == section_id, PaperSection.paper_id == paper.id
        )
    )
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    paper.status = "analyzing"
    db.commit()

    try:
        analyze_section_task.delay(section.id)
    except Exception as exc:
        db.rollback()
        paper.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analysis could not be started. Please try again later.",
        ) from exc

    db.refresh(paper)

    return paper


@router.get("/{paper_id}/questions", response_model=list[PaperQuestionRead])
def list_paper_questions(
    paper_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PaperQuestion]:
    paper = db.scalar(
        select(Paper).where(Paper.id == paper_id, Paper.user_id == current_user.id)
    )
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    questions = db.scalars(
        select(PaperQuestion)
        .where(PaperQuestion.paper_id == paper.id)
        .order_by(PaperQuestion.created_at.asc())
    ).all()
    return list(questions)


@router.post("/{paper_id}/ask", response_model=PaperQuestionRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("15/minute")
def ask_paper_question(
    request: Request,
    paper_id: int,
    payload: PaperQuestionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaperQuestion:
    paper = db.scalar(
        select(Paper)
        .options(selectinload(Paper.sections))
        .where(Paper.id == paper_id, Paper.user_id == current_user.id)
    )
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    if not paper.sections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paper has no extracted content to answer from",
        )

    answer, provider = answer_question(paper, payload.question.strip())
    record = PaperQuestion(
        paper_id=paper.id,
        question=payload.question.strip(),
        answer=answer,
        provider=provider,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paper(
    paper_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    paper = db.scalar(
        select(Paper).where(Paper.id == paper_id, Paper.user_id == current_user.id)
    )
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    file_path = _get_upload_dir() / paper.stored_filename
    db.delete(paper)
    db.commit()
    file_path.unlink(missing_ok=True)
