from uuid import uuid4

from app.conversations.repository import (
    ConversationRepository,
)


class ConversationService:
    """
    Service responsable du cycle de vie
    des conversations.
    """

    def __init__(
        self,
        repository: ConversationRepository,
    ) -> None:
        self._repository = repository

    def create_conversation(
        self,
        title: str | None = None,
    ) -> dict:
        """
        Crée une nouvelle conversation.
        """

        conversation = {
            "id": str(uuid4()),
            "title": title or "Nouvelle conversation",
        }

        self._repository.save(
            conversation
        )

        return conversation

    def get_conversations(self) -> list[dict]:
        """
        Retourne toutes les conversations.
        """

        return self._repository.get_all()

    def get_conversation(
        self,
        conversation_id: str,
    ) -> dict | None:
        """
        Retourne une conversation à partir de son identifiant.
        """

        return self._repository.get_by_id(
            conversation_id
        )