from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    type: str
    page_count: int
    size: int
    created_at: datetime
    status: str