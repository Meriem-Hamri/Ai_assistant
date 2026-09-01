from uuid import uuid4

from app.conversations.message_repository import MessageRepository


class MessageService:
    """Service métier des messages de conversation."""

    _ALLOWED_ROLES = {"user", "assistant"}

    def __init__(self, repository: MessageRepository) -> None:
        self._repository = repository

    def create_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: list[dict] | None = None,
    ) -> dict:
        if role not in self._ALLOWED_ROLES:
            raise ValueError("Le rôle doit être 'user' ou 'assistant'.")

        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("Le contenu du message ne peut pas être vide.")

        return self._repository.save(
            {
                "id": str(uuid4()),
                "conversation_id": conversation_id,
                "role": role,
                "content": normalized_content,
                "sources": sources,
            }
        )

    def get_messages(self, conversation_id: str) -> list[dict]:
        return self._repository.get_by_conversation(conversation_id)
