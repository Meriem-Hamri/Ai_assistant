from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    get_conversation_service,
    get_document_repository,
    get_message_service,
    get_rag_pipeline,
)
from app.api.schemas.chat import ChatRequest, ChatResponse
from app.chat.service import (
    ChatService,
    ChatDocumentNotFoundError,
    ChatDocumentNotReadyError,
    ConversationNotFoundError,
    InvalidChatQuestionError,
)
from app.conversations.message_service import MessageService
from app.conversations.service import ConversationService
from app.documents.repository import DocumentRepository
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
    document_repository: DocumentRepository = Depends(
        get_document_repository
    ),
) -> ChatService:

    return ChatService(
        rag_pipeline=rag_pipeline,
        conversation_service=conversation_service,
        message_service=message_service,
        document_repository=document_repository,
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
            document_ids=data.document_ids,
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
    except ChatDocumentNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Document introuvable.",
        ) from exc
    except ChatDocumentNotReadyError as exc:
        raise HTTPException(
            status_code=409,
            detail=(
                "Un ou plusieurs documents sélectionnés ne sont pas prêts."
            ),
        ) from exc
    except InvalidChatQuestionError as exc:
        raise HTTPException(
            status_code=400,
            detail="La question ne peut pas être vide.",
        ) from exc
