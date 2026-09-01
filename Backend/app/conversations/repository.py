from uuid import UUID

from sqlalchemy import select

from app.database.models.conversation import ConversationModel
from app.database.session import SessionLocal


class ConversationRepository:
    """Persiste les conversations dans PostgreSQL."""

    _UPDATABLE_FIELDS = {"title", "active_document_id", "updated_at"}

    def save(self, conversation: dict) -> dict:
        """Enregistre une conversation et retourne sa représentation persistée."""
        model = ConversationModel(
            id=UUID(conversation["id"]),
            title=conversation["title"],
            active_document_id=self._parse_optional_id(
                conversation.get("active_document_id")
            ),
        )

        if conversation.get("created_at") is not None:
            model.created_at = conversation["created_at"]
        if conversation.get("updated_at") is not None:
            model.updated_at = conversation["updated_at"]

        with SessionLocal() as session:
            try:
                session.add(model)
                session.commit()
                return self._to_dict(model)
            except Exception:
                session.rollback()
                raise

    def get_all(self) -> list[dict]:
        """Retourne les conversations dans un ordre récent déterministe."""
        with SessionLocal() as session:
            conversations = session.scalars(
                select(ConversationModel).order_by(
                    ConversationModel.updated_at.desc(),
                    ConversationModel.created_at.desc(),
                    ConversationModel.id.desc(),
                )
            ).all()
            return [self._to_dict(conversation) for conversation in conversations]

    def get_by_id(self, conversation_id: str) -> dict | None:
        """Retourne une conversation, ou None pour un identifiant invalide/absent."""
        parsed_id = self._parse_id(conversation_id)
        if parsed_id is None:
            return None

        with SessionLocal() as session:
            conversation = session.get(ConversationModel, parsed_id)
            if conversation is None:
                return None
            return self._to_dict(conversation)

    def update(self, conversation_id: str, updates: dict) -> dict | None:
        """Met à jour les seuls champs autorisés d'une conversation."""
        parsed_id = self._parse_id(conversation_id)
        if parsed_id is None:
            return None

        with SessionLocal() as session:
            try:
                conversation = session.get(ConversationModel, parsed_id)
                if conversation is None:
                    return None

                for field, value in updates.items():
                    if field not in self._UPDATABLE_FIELDS:
                        continue
                    if field == "active_document_id":
                        value = self._parse_optional_id(value)
                    setattr(conversation, field, value)

                session.commit()
                return self._to_dict(conversation)
            except Exception:
                session.rollback()
                raise

    def delete(self, conversation_id: str) -> bool:
        """Supprime une conversation existante."""
        parsed_id = self._parse_id(conversation_id)
        if parsed_id is None:
            return False

        with SessionLocal() as session:
            try:
                conversation = session.get(ConversationModel, parsed_id)
                if conversation is None:
                    return False

                session.delete(conversation)
                session.commit()
                return True
            except Exception:
                session.rollback()
                raise

    @staticmethod
    def _parse_id(value: str) -> UUID | None:
        try:
            return UUID(value)
        except (AttributeError, TypeError, ValueError):
            return None

    @staticmethod
    def _parse_optional_id(value: str | None) -> UUID | None:
        if value is None:
            return None
        return UUID(value)

    @staticmethod
    def _to_dict(conversation: ConversationModel) -> dict:
        return {
            "id": str(conversation.id),
            "title": conversation.title,
            "active_document_id": (
                str(conversation.active_document_id)
                if conversation.active_document_id is not None
                else None
            ),
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        }
