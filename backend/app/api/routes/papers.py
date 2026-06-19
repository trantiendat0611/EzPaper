from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.paper import Paper
from app.models.user import User
from app.schemas.paper import PaperAnalysisResult, PaperDetail, PaperList, PaperRead
from app.services.pdf_processor import process_uploaded_pdf
from app.services.section_analyzer import analyze_paper_sections

router = APIRouter(prefix="/papers", tags=["papers"])


def _get_upload_dir() -> Path:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _validate_pdf(file: UploadFile) -> None:
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


@router.post("/upload", response_model=PaperRead, status_code=status.HTTP_201_CREATED)
async def upload_paper(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Paper:
    _validate_pdf(file)

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

    paper = process_uploaded_pdf(db, paper, destination)

    return paper


@router.get("", response_model=PaperList)
def list_papers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaperList:
    papers = db.scalars(
        select(Paper)
        .where(Paper.user_id == current_user.id)
        .order_by(Paper.created_at.desc())
    ).all()
    return PaperList(items=list(papers))


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


@router.post("/{paper_id}/analyze", response_model=PaperAnalysisResult)
def analyze_paper(
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

    analyzed_paper, provider = analyze_paper_sections(db, paper)
    result = PaperDetail.model_validate(analyzed_paper).model_dump()
    return PaperAnalysisResult(**result, analysis_provider=provider)


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
