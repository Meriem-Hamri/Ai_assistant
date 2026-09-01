from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.chat import get_chat_service, router
from app.api.schemas.chat import ChatResponse, ChatSourceResponse
from app.chat.service import (
    ConversationNotFoundError,
    InvalidChatQuestionError,
)


CONVERSATION_ID = "4c90d6fd-56d6-42d4-bd73-e10bfc621851"


class FakeChatService:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.received_kwargs = None

    def send_message(self, **kwargs):
        self.received_kwargs = kwargs
        if self.error:
            raise self.error
        return self.result


def make_client(service):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_chat_service] = lambda: service
    return TestClient(app)


def test_conversation_id_is_required():
    service = FakeChatService()

    response = make_client(service).post(
        "/chat/",
        json={"question": "Question"},
    )

    assert response.status_code == 422
    assert service.received_kwargs is None


def test_missing_conversation_returns_404():
    service = FakeChatService(error=ConversationNotFoundError())

    response = make_client(service).post(
        "/chat/",
        json={
            "conversation_id": CONVERSATION_ID,
            "question": "Question",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation introuvable."}


def test_success_returns_conversation_answer_and_sources():
    source = ChatSourceResponse(
        document_id="document-1",
        document_name="contrat.pdf",
        page_number=4,
        chunk_id="chunk-4",
        excerpt="Extrait",
        distance=0.12,
    )
    service = FakeChatService(
        result=ChatResponse(
            conversation_id=CONVERSATION_ID,
            answer="Reponse",
            sources=[source],
        )
    )

    response = make_client(service).post(
        "/chat/",
        json={
            "conversation_id": CONVERSATION_ID,
            "question": "Question",
            "document_id": "document-1",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "conversation_id": CONVERSATION_ID,
        "answer": "Reponse",
        "sources": [source.model_dump()],
    }
    assert service.received_kwargs["conversation_id"] == CONVERSATION_ID
    assert service.received_kwargs["document_id"] == "document-1"


def test_blank_question_returns_400():
    service = FakeChatService(error=InvalidChatQuestionError())

    response = make_client(service).post(
        "/chat/",
        json={
            "conversation_id": CONVERSATION_ID,
            "question": "   ",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "La question ne peut pas être vide."
    }
