from fastapi import APIRouter, Depends,HTTPException

from app.api.dependencies import (
    get_conversation_repository,
)
from app.api.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
)
from app.conversations.repository import (
    ConversationRepository,
)
from app.conversations.service import (
    ConversationService,
)


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


def get_conversation_service(
    repository: ConversationRepository = Depends(
        get_conversation_repository
    ),
) -> ConversationService:

    return ConversationService(
        repository=repository
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