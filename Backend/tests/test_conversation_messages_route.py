from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_conversation_service,
    get_message_service,
)
from app.api.routes.conversations import router


CONVERSATION_ID = "4c90d6fd-56d6-42d4-bd73-e10bfc621851"
MISSING_CONVERSATION_ID = "e11ade2f-9ca2-4db5-b2d8-596851479c78"
CREATED_AT = datetime(2026, 8, 31, 14, 30, tzinfo=timezone.utc)
UPDATED_AT = datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc)


class FakeConversationService:
    def __init__(self, conversation):
        self.conversation = conversation
        self.requested_ids = []
        self.mutation_calls = []

    def get_conversation(self, conversation_id):
        self.requested_ids.append(conversation_id)
        return self.conversation

    def create_conversation(self, *args, **kwargs):
        self.mutation_calls.append(("create", args, kwargs))
        return self.conversation

    def get_conversations(self):
        return [self.conversation] if self.conversation is not None else []

    def update_conversation(self, *args, **kwargs):
        self.mutation_calls.append(("update", args, kwargs))

    def delete_conversation(self, *args, **kwargs):
        self.mutation_calls.append(("delete", args, kwargs))
        return self.conversation is not None


class FakeMessageService:
    def __init__(self, messages=None):
        self.messages = messages or []
        self.requested_ids = []
        self.mutation_calls = []

    def get_messages(self, conversation_id):
        self.requested_ids.append(conversation_id)
        return self.messages

    def create_message(self, *args, **kwargs):
        self.mutation_calls.append(("create", args, kwargs))


def make_client(conversation_service, message_service):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_conversation_service] = (
        lambda: conversation_service
    )
    app.dependency_overrides[get_message_service] = lambda: message_service
    return TestClient(app)


def make_message(**overrides):
    message = {
        "id": "message-1",
        "conversation_id": CONVERSATION_ID,
        "role": "user",
        "content": "Question",
        "sources": None,
        "document_ids": [],
        "created_at": CREATED_AT,
    }
    message.update(overrides)
    return message


def make_conversation():
    return {
        "id": CONVERSATION_ID,
        "title": "Première question",
        "active_document_id": None,
        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT,
    }


def assert_complete_conversation_response(data):
    assert data == {
        "id": CONVERSATION_ID,
        "title": "Première question",
        "active_document_id": None,
        "created_at": CREATED_AT.isoformat().replace("+00:00", "Z"),
        "updated_at": UPDATED_AT.isoformat().replace("+00:00", "Z"),
    }


def test_create_conversation_returns_complete_contract():
    conversation_service = FakeConversationService(make_conversation())

    response = make_client(conversation_service, FakeMessageService()).post(
        "/conversations/",
        json={"title": "Première question"},
    )

    assert response.status_code == 200
    assert_complete_conversation_response(response.json())
    assert conversation_service.mutation_calls == [
        ("create", (), {"title": "Première question"})
    ]


def test_list_conversations_returns_complete_contract():
    conversation_service = FakeConversationService(make_conversation())

    response = make_client(conversation_service, FakeMessageService()).get(
        "/conversations/"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert_complete_conversation_response(response.json()[0])


def test_get_conversation_returns_complete_contract():
    conversation_service = FakeConversationService(make_conversation())

    response = make_client(conversation_service, FakeMessageService()).get(
        f"/conversations/{CONVERSATION_ID}"
    )

    assert response.status_code == 200
    assert_complete_conversation_response(response.json())


def test_missing_conversation_returns_404_without_reading_messages():
    conversation_service = FakeConversationService(None)
    message_service = FakeMessageService()

    response = make_client(conversation_service, message_service).get(
        f"/conversations/{MISSING_CONVERSATION_ID}/messages"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation introuvable."}
    assert conversation_service.requested_ids == [MISSING_CONVERSATION_ID]
    assert message_service.requested_ids == []


def test_invalid_uuid_returns_404_without_reading_messages():
    conversation_service = FakeConversationService(None)
    message_service = FakeMessageService()

    response = make_client(conversation_service, message_service).get(
        "/conversations/uuid-invalide/messages"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation introuvable."}
    assert conversation_service.requested_ids == ["uuid-invalide"]
    assert message_service.requested_ids == []


def test_existing_empty_conversation_returns_empty_list():
    conversation_service = FakeConversationService({"id": CONVERSATION_ID})
    message_service = FakeMessageService()

    response = make_client(conversation_service, message_service).get(
        f"/conversations/{CONVERSATION_ID}/messages"
    )

    assert response.status_code == 200
    assert response.json() == []
    assert message_service.requested_ids == [CONVERSATION_ID]


def test_user_message_normalizes_null_sources_to_empty_list():
    conversation_service = FakeConversationService({"id": CONVERSATION_ID})
    message_service = FakeMessageService([make_message()])

    response = make_client(conversation_service, message_service).get(
        f"/conversations/{CONVERSATION_ID}/messages"
    )

    assert response.status_code == 200
    assert response.json()[0]["sources"] == []
    assert response.json()[0]["document_ids"] == []


def test_user_message_exposes_selected_document_snapshot():
    conversation_service = FakeConversationService({"id": CONVERSATION_ID})
    message_service = FakeMessageService(
        [make_message(document_ids=["A", "B"])]
    )

    response = make_client(conversation_service, message_service).get(
        f"/conversations/{CONVERSATION_ID}/messages"
    )

    assert response.status_code == 200
    assert response.json()[0]["document_ids"] == ["A", "B"]


def test_assistant_message_returns_complete_source_snapshot():
    source = {
        "document_id": "document-1",
        "document_name": "contrat.pdf",
        "page_number": 4,
        "chunk_id": "chunk-4",
        "excerpt": "Extrait",
        "distance": 0.12,
    }
    conversation_service = FakeConversationService({"id": CONVERSATION_ID})
    message_service = FakeMessageService(
        [
            make_message(
                role="assistant",
                content="Reponse",
                sources=[source],
            )
        ]
    )

    response = make_client(conversation_service, message_service).get(
        f"/conversations/{CONVERSATION_ID}/messages"
    )

    assert response.status_code == 200
    assert response.json()[0]["sources"] == [source]
    assert response.json()[0]["document_ids"] == []


def test_message_order_is_preserved_and_read_does_not_mutate():
    conversation_service = FakeConversationService({"id": CONVERSATION_ID})
    message_service = FakeMessageService(
        [
            make_message(id="message-2", content="Deuxieme"),
            make_message(id="message-1", content="Premier"),
        ]
    )

    response = make_client(conversation_service, message_service).get(
        f"/conversations/{CONVERSATION_ID}/messages"
    )

    assert response.status_code == 200
    assert [message["id"] for message in response.json()] == [
        "message-2",
        "message-1",
    ]
    assert conversation_service.mutation_calls == []
    assert message_service.mutation_calls == []


def test_delete_conversation_uses_existing_service():
    conversation_service = FakeConversationService(make_conversation())
    response = make_client(conversation_service, FakeMessageService()).delete(
        f"/conversations/{CONVERSATION_ID}"
    )
    assert response.status_code == 200
    assert conversation_service.mutation_calls == [
        ("delete", (CONVERSATION_ID,), {})
    ]


def test_delete_missing_conversation_returns_404():
    response = make_client(
        FakeConversationService(None), FakeMessageService()
    ).delete(f"/conversations/{MISSING_CONVERSATION_ID}")
    assert response.status_code == 404
