from datetime import datetime

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    filename: str
    type: str
    page_count: int
    size: int
    created_at: datetime
    status: str
    title: str | None = None
    category: str | None = None
    year: int | None = None
    person: str | None = None
    department: str | None = None
    document_type: str | None = None
    tags: list[str] = Field(default_factory=list)
