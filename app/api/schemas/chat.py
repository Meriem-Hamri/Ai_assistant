from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str
    document_id: str | None = None
    category: str | None = None
    year: int | None = Field(default=None, ge=1000, le=9999)
    person: str | None = None
    tags: list[str] | None = None
    department: str | None = None
    document_type: str | None = None


class ChatSourceResponse(BaseModel):
    document_id: str
    document_name: str
    page_number: int | None
    distance: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSourceResponse]
