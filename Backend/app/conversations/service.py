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

        normalized_title = title.strip() if title else ""
        if len(normalized_title) > 80:
            normalized_title = f"{normalized_title[:77]}..."
        conversation = {
            "id": str(uuid4()),
            "title": normalized_title or "Nouvelle conversation",
        }

        return self._repository.save(conversation)

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

    def update_conversation(
        self,
        conversation_id: str,
        updates: dict,
    ) -> dict | None:
        """Met à jour une conversation existante."""
        return self._repository.update(conversation_id, updates)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Supprime une conversation existante."""
        return self._repository.delete(conversation_id)
