from fastapi import APIRouter, Depends

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