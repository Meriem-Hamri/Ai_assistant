from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.models.message import MessageModel
from app.database.models.message_document import MessageDocumentModel
from app.database.session import SessionLocal


class MessageRepository:
    """Persiste les messages de conversation dans PostgreSQL."""

    def save(self, message: dict) -> dict:
        """Enregistre un message et retourne sa représentation persistée."""
        model = MessageModel(
            id=UUID(message["id"]),
            conversation_id=UUID(message["conversation_id"]),
            role=message["role"],
            content=message["content"],
            sources=message.get("sources"),
            document_links=[
                MessageDocumentModel(
                    document_id=UUID(document_id),
                    position=position,
                )
                for position, document_id in enumerate(
                    message.get("document_ids") or []
                )
            ],
        )

        if message.get("created_at") is not None:
            model.created_at = message["created_at"]

        with SessionLocal() as session:
            try:
                session.add(model)
                session.commit()
                return self._to_dict(model)
            except Exception:
                session.rollback()
                raise

    def get_by_id(self, message_id: str) -> dict | None:
        """Retourne un message, ou None pour un identifiant invalide/absent."""
        parsed_id = self._parse_id(message_id)
        if parsed_id is None:
            return None

        with SessionLocal() as session:
            message = session.scalar(
                select(MessageModel)
                .options(selectinload(MessageModel.document_links))
                .where(MessageModel.id == parsed_id)
            )
            if message is None:
                return None
            return self._to_dict(message)

    def get_by_conversation(self, conversation_id: str) -> list[dict]:
        """Retourne les messages d'une conversation dans l'ordre chronologique."""
        parsed_id = self._parse_id(conversation_id)
        if parsed_id is None:
            return []

        with SessionLocal() as session:
            messages = session.scalars(
                select(MessageModel)
                .options(selectinload(MessageModel.document_links))
                .where(MessageModel.conversation_id == parsed_id)
                .order_by(
                    MessageModel.created_at.asc(),
                    MessageModel.id.asc(),
                )
            ).all()
            return [self._to_dict(message) for message in messages]

    @staticmethod
    def _parse_id(value: str) -> UUID | None:
        try:
            return UUID(value)
        except (AttributeError, TypeError, ValueError):
            return None

    @staticmethod
    def _to_dict(message: MessageModel) -> dict:
        return {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "role": message.role,
            "content": message.content,
            "sources": message.sources,
            "document_ids": [
                str(link.document_id) for link in message.document_links
            ],
            "created_at": message.created_at,
        }
