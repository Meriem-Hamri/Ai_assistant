from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.conversations.message_service import MessageService
from app.conversations.service import ConversationService


class RecordingRepository:
    def __init__(self):
        self.saved = []

    def save(self, data):
        self.saved.append(data)
        return {**data, "created_at": datetime.now(timezone.utc)}

    def get_all(self):
        return ["all"]

    def get_by_id(self, item_id):
        return {"id": item_id}

    def get_by_conversation(self, conversation_id):
        return [{"conversation_id": conversation_id}]

    def update(self, item_id, updates):
        return {"id": item_id, **updates}

    def delete(self, item_id):
        return item_id == "existing"


@pytest.mark.parametrize("title", [None, "", "   "])
def test_conversation_service_normalizes_blank_title(title):
    repository = RecordingRepository()
    service = ConversationService(repository)

    result = service.create_conversation(title)

    UUID(result["id"])
    assert result["title"] == "Nouvelle conversation"
    assert "created_at" in result


def test_conversation_service_normalizes_title_and_delegates_lifecycle():
    repository = RecordingRepository()
    service = ConversationService(repository)

    created = service.create_conversation("  Mon titre  ")

    assert created["title"] == "Mon titre"
    assert service.get_conversations() == ["all"]
    assert service.get_conversation("id") == {"id": "id"}
    assert service.update_conversation("id", {"title": "Nouveau"}) == {
        "id": "id",
        "title": "Nouveau",
    }
    assert service.delete_conversation("existing") is True


@pytest.mark.parametrize("role", ["user", "assistant"])
def test_message_service_accepts_roles_and_strips_content(role):
    repository = RecordingRepository()
    service = MessageService(repository)
    sources = [{"document_id": "doc"}] if role == "assistant" else None

    result = service.create_message("conversation", role, "  Contenu  ", sources)

    UUID(result["id"])
    assert result["conversation_id"] == "conversation"
    assert result["role"] == role
    assert result["content"] == "Contenu"
    assert result["sources"] == sources


def test_message_service_rejects_invalid_role_and_blank_content():
    service = MessageService(RecordingRepository())

    with pytest.raises(ValueError):
        service.create_message("conversation", "system", "Contenu")
    with pytest.raises(ValueError):
        service.create_message("conversation", "user", "   ")


def test_message_service_get_messages_delegates_to_repository():
    service = MessageService(RecordingRepository())

    assert service.get_messages("conversation") == [
        {"conversation_id": "conversation"}
    ]
