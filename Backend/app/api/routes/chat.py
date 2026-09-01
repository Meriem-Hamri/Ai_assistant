from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    get_conversation_service,
    get_message_service,
    get_rag_pipeline,
)
from app.api.schemas.chat import ChatRequest, ChatResponse
from app.chat.service import (
    ChatService,
    ConversationNotFoundError,
    InvalidChatQuestionError,
)
from app.conversations.message_service import MessageService
from app.conversations.service import ConversationService
from app.rag.pipeline import RAGPipeline


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


def get_chat_service(
    rag_pipeline: RAGPipeline = Depends(
        get_rag_pipeline
    ),
    conversation_service: ConversationService = Depends(
        get_conversation_service
    ),
    message_service: MessageService = Depends(
        get_message_service
    ),
) -> ChatService:

    return ChatService(
        rag_pipeline=rag_pipeline,
        conversation_service=conversation_service,
        message_service=message_service,
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
    try:
        return service.send_message(
            conversation_id=data.conversation_id,
            question=data.question,
            document_id=data.document_id,
            category=data.category,
            year=data.year,
            person=data.person,
            tags=data.tags,
            department=data.department,
            document_type=data.document_type,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Conversation introuvable.",
        ) from exc
    except InvalidChatQuestionError as exc:
        raise HTTPException(
            status_code=400,
            detail="La question ne peut pas être vide.",
        ) from exc
