from datetime import datetime

from pydantic import BaseModel

from app.api.schemas.chat import ChatSourceResponse


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    active_document_id: str | None
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: list[ChatSourceResponse]
    created_at: datetime
