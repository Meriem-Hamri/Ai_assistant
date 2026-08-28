from fastapi import APIRouter, Depends

from app.api.dependencies import get_rag_pipeline
from app.api.schemas.chat import ChatRequest, ChatResponse
from app.chat.service import ChatService
from app.rag.pipeline import RAGPipeline


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


def get_chat_service(
    rag_pipeline: RAGPipeline = Depends(
        get_rag_pipeline
    ),
) -> ChatService:

    return ChatService(
        rag_pipeline=rag_pipeline
    )


@router.post(
    "/",
    response_model=ChatResponse,
)
def send_message(
    data: ChatRequest,
    service: ChatService = Depends(
        get_chat_service
    ),
):
    return service.send_message(
        question=data.question,
        document_id=data.document_id,
    )