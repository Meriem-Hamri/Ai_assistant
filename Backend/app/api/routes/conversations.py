from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    get_conversation_service,
    get_message_service,
)
from app.api.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    MessageResponse,
)
from app.conversations.message_service import MessageService
from app.conversations.service import ConversationService


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.post(
    "/",
    response_model=ConversationResponse,
)
def create_conversation(
    data: ConversationCreate,
    service: ConversationService = Depends(
        get_conversation_service
    ),
):
    return service.create_conversation(
        title=data.title
    )


@router.get(
    "/",
    response_model=list[ConversationResponse],
)
def list_conversations(
    service: ConversationService = Depends(
        get_conversation_service
    ),
):
    return service.get_conversations()


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: str,
    service: ConversationService = Depends(
        get_conversation_service
    ),
):
    conversation = service.get_conversation(
        conversation_id
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation introuvable.",
        )

    return conversation


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def get_conversation_messages(
    conversation_id: str,
    conversation_service: ConversationService = Depends(
        get_conversation_service
    ),
    message_service: MessageService = Depends(
        get_message_service
    ),
):
    conversation = conversation_service.get_conversation(
        conversation_id
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation introuvable.",
        )

    messages = message_service.get_messages(conversation_id)
    return [
        MessageResponse(
            **{
                **message,
                "sources": message.get("sources") or [],
                "document_ids": message.get("document_ids") or [],
            }
        )
        for message in messages
    ]


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
):
    if not service.delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation introuvable.")
    return {"message": "Conversation supprimée avec succès."}
