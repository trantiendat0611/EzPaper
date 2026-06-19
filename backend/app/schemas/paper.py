from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PaperRead(BaseModel):
    id: int
    title: str
    original_filename: str
    status: str
    abstract: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaperList(BaseModel):
    items: list[PaperRead]


class PaperSectionRead(BaseModel):
    id: int
    title: str
    section_type: str
    order_index: int
    raw_text: str
    summary_vi: str | None
    explanation_vi: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaperDetail(PaperRead):
    sections: list[PaperSectionRead]


class PaperAnalysisResult(PaperDetail):
    analysis_provider: str
