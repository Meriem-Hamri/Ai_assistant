from datetime import datetime

from pydantic import BaseModel, Field

from app.extraction.ocr_language import OcrLanguage


class DocumentResponse(BaseModel):
    id: str
    filename: str
    type: str
    page_count: int | None = None
    size: int
    created_at: datetime
    status: str
    error_message: str | None = None
    chunk_count: int | None = None
    title: str | None = None
    category: str | None = None
    year: int | None = None
    person: str | None = None
    department: str | None = None
    document_type: str | None = None
    tags: list[str] = Field(default_factory=list)
    ocr_language: OcrLanguage = "fr"


class DocumentMetadataOptionsResponse(BaseModel):
    category: list[str]
    department: list[str]
    document_type: list[str]
