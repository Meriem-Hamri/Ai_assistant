from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    document_id: str


class ChatSourceResponse(BaseModel):
    document_id: str
    document_name: str
    page_number: int | None
    distance: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSourceResponse]