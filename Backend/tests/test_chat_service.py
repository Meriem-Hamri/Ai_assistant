from datetime import datetime, timezone

import pytest

from app.chat.service import (
    ChatDocumentNotFoundError,
    ChatDocumentNotReadyError,
    ChatService,
    ConversationNotFoundError,
    InvalidChatQuestionError,
)
from app.conversations.message_service import (
    EmptyMessageContentError,
    InvalidMessageRoleError,
)
from app.rag.exceptions import RAGGenerationError
from app.rag.response import RAGResponse, Source


CONVERSATION_ID = "4c90d6fd-56d6-42d4-bd73-e10bfc621851"


class FakeConversationService:
    def __init__(self, conversation=None, operations=None):
        self.conversation = conversation
        self.operations = operations if operations is not None else []
        self.updates = []

    def get_conversation(self, conversation_id):
        self.operations.append(("get_conversation", conversation_id))
        return self.conversation

    def update_conversation(self, conversation_id, updates):
        self.operations.append(("update_conversation", conversation_id))
        self.updates.append((conversation_id, updates))
        return {**self.conversation, **updates}


class FakeMessageService:
    def __init__(self, operations=None, assistant_error=None):
        self.operations = operations if operations is not None else []
        self.assistant_error = assistant_error
        self.created = []

    def create_message(self, **message):
        self.operations.append(("create_message", message["role"]))
        if message["role"] == "assistant" and self.assistant_error:
            raise self.assistant_error

        persisted = {**message, "content": message["content"].strip()}
        self.created.append(persisted)
        return persisted


class FakeRAGPipeline:
    def __init__(self, response=None, error=None, operations=None):
        self.response = response or RAGResponse(
            answer="Le salaire est de 9 500 DH.",
            sources=[
                Source(
                    document_id="document-1",
                    document_name="contrat.pdf",
                    page_number=4,
                    chunk_id="chunk-4",
                    excerpt="Le salaire mensuel brut est fixe a 9 500 DH.",
                    distance=0.12,
                )
            ],
        )
        self.error = error
        self.operations = operations if operations is not None else []
        self.received_kwargs = None

    def answer(self, **kwargs):
        self.operations.append(("rag", kwargs["question"]))
        self.received_kwargs = kwargs
        if self.error:
            raise self.error
        return self.response


class FakeDocumentRepository:
    def __init__(self, documents=None, operations=None):
        self.documents = documents or {}
        self.operations = operations if operations is not None else []
        self.received_ids = []

    def get_by_ids(self, document_ids):
        ids = list(document_ids)
        self.operations.append(("get_documents", tuple(ids)))
        self.received_ids.append(ids)
        return [self.documents[value] for value in ids if value in self.documents]


def build_service(
    *,
    conversation=None,
    rag_response=None,
    rag_error=None,
    assistant_error=None,
    documents=None,
):
    operations = []
    conversation_service = FakeConversationService(
        conversation=conversation,
        operations=operations,
    )
    message_service = FakeMessageService(
        operations=operations,
        assistant_error=assistant_error,
    )
    rag_pipeline = FakeRAGPipeline(
        response=rag_response,
        error=rag_error,
        operations=operations,
    )
    document_repository = FakeDocumentRepository(
        documents=documents,
        operations=operations,
    )
    service = ChatService(
        rag_pipeline=rag_pipeline,
        conversation_service=conversation_service,
        message_service=message_service,
        document_repository=document_repository,
    )
    return (
        service,
        conversation_service,
        message_service,
        rag_pipeline,
        document_repository,
        operations,
    )


@pytest.mark.parametrize("conversation_id", [CONVERSATION_ID, "invalid-uuid"])
def test_missing_or_invalid_conversation_stops_before_message_and_rag(
    conversation_id,
):
    (
        service,
        conversations,
        messages,
        rag,
        documents,
        operations,
    ) = build_service()

    with pytest.raises(ConversationNotFoundError):
        service.send_message(conversation_id, "Question")

    assert operations == [("get_conversation", conversation_id)]
    assert messages.created == []
    assert rag.received_kwargs is None
    assert documents.received_ids == []
    assert conversations.updates == []


def test_success_persists_messages_sources_and_updates_after_assistant():
    service, conversations, messages, rag, _, operations = build_service(
        conversation={"id": CONVERSATION_ID},
        documents={
            "document-1": {"id": "document-1", "status": "ready"},
        },
    )

    response = service.send_message(
        conversation_id=CONVERSATION_ID,
        question="   Quel est le salaire ?   ",
        document_ids=["document-1"],
        category="finance",
        year=2016,
        person="Ahmed",
        tags=["salaire", "contrat"],
        department="RH",
        document_type="contrat",
    )

    expected_source = {
        "document_id": "document-1",
        "document_name": "contrat.pdf",
        "page_number": 4,
        "chunk_id": "chunk-4",
        "excerpt": "Le salaire mensuel brut est fixe a 9 500 DH.",
        "distance": 0.12,
    }
    assert operations == [
        ("get_conversation", CONVERSATION_ID),
        ("get_documents", ("document-1",)),
        ("create_message", "user"),
        ("rag", "Quel est le salaire ?"),
        ("create_message", "assistant"),
        ("update_conversation", CONVERSATION_ID),
    ]
    assert messages.created == [
        {
            "conversation_id": CONVERSATION_ID,
            "role": "user",
            "content": "Quel est le salaire ?",
            "sources": None,
            "document_ids": ["document-1"],
        },
        {
            "conversation_id": CONVERSATION_ID,
            "role": "assistant",
            "content": "Le salaire est de 9 500 DH.",
            "sources": [expected_source],
            "document_ids": [],
        },
    ]
    filters = rag.received_kwargs["filters"]
    assert rag.received_kwargs["question"] == "Quel est le salaire ?"
    assert rag.received_kwargs["document_ids"] == ("document-1",)
    assert filters.category == "finance"
    assert filters.year == 2016
    assert filters.person == "Ahmed"
    assert filters.tags == ("salaire", "contrat")
    assert filters.department == "RH"
    assert filters.document_type == "contrat"
    assert conversations.updates[0][0] == CONVERSATION_ID
    assert conversations.updates[0][1].keys() == {"updated_at"}
    updated_at = conversations.updates[0][1]["updated_at"]
    assert isinstance(updated_at, datetime)
    assert updated_at.tzinfo == timezone.utc
    assert response.conversation_id == CONVERSATION_ID
    assert response.answer == "Le salaire est de 9 500 DH."
    assert [source.model_dump() for source in response.sources] == [
        expected_source
    ]
    assert response.sources[0].model_dump() == (
        messages.created[1]["sources"][0]
    )


def test_empty_selection_skips_document_lookup_and_means_all_documents():
    service, _, messages, rag, documents, operations = build_service(
        conversation={"id": CONVERSATION_ID}
    )

    service.send_message(CONVERSATION_ID, "Question", document_ids=[])

    assert documents.received_ids == []
    assert messages.created[0]["document_ids"] == []
    assert rag.received_kwargs["document_ids"] == ()
    assert operations[:3] == [
        ("get_conversation", CONVERSATION_ID),
        ("create_message", "user"),
        ("rag", "Question"),
    ]


def test_multiple_documents_are_normalized_once_for_snapshot_and_rag():
    service, _, messages, rag, documents, _ = build_service(
        conversation={"id": CONVERSATION_ID},
        documents={
            "A": {"id": "A", "status": "ready"},
            "B": {"id": "B", "status": "ready"},
        },
    )

    service.send_message(
        CONVERSATION_ID,
        "Question",
        document_ids=[" A ", "", "A", " B "],
    )

    assert documents.received_ids == [["A", "B"]]
    assert messages.created[0]["document_ids"] == ["A", "B"]
    assert rag.received_kwargs["document_ids"] == ("A", "B")
    assert messages.created[1]["document_ids"] == []


@pytest.mark.parametrize(
    "requested_ids",
    [["missing"], ["A", "missing"]],
)
def test_missing_document_stops_before_message_rag_and_update(requested_ids):
    (
        service,
        conversations,
        messages,
        rag,
        documents,
        operations,
    ) = build_service(
        conversation={"id": CONVERSATION_ID},
        documents={"A": {"id": "A", "status": "ready"}},
    )

    with pytest.raises(ChatDocumentNotFoundError):
        service.send_message(
            CONVERSATION_ID,
            "Question",
            document_ids=requested_ids,
        )

    assert documents.received_ids == [requested_ids]
    assert messages.created == []
    assert rag.received_kwargs is None
    assert conversations.updates == []
    assert all(operation[0] != "create_message" for operation in operations)


@pytest.mark.parametrize("status", ["queued", "processing", "error", "other"])
def test_non_ready_document_stops_before_message_rag_and_update(status):
    service, conversations, messages, rag, _, _ = build_service(
        conversation={"id": CONVERSATION_ID},
        documents={"A": {"id": "A", "status": status}},
    )

    with pytest.raises(ChatDocumentNotReadyError):
        service.send_message(CONVERSATION_ID, "Question", document_ids=["A"])

    assert messages.created == []
    assert rag.received_kwargs is None
    assert conversations.updates == []


def test_rag_failure_keeps_user_and_does_not_update_conversation():
    error = RAGGenerationError("generation indisponible")
    service, conversations, messages, _, _, operations = build_service(
        conversation={"id": CONVERSATION_ID},
        rag_error=error,
        documents={"A": {"id": "A", "status": "ready"}},
    )

    with pytest.raises(RAGGenerationError) as raised:
        service.send_message(CONVERSATION_ID, "Question", document_ids=["A"])

    assert raised.value is error
    assert [message["role"] for message in messages.created] == ["user"]
    assert messages.created[0]["document_ids"] == ["A"]
    assert conversations.updates == []
    assert operations == [
        ("get_conversation", CONVERSATION_ID),
        ("get_documents", ("A",)),
        ("create_message", "user"),
        ("rag", "Question"),
    ]


def test_assistant_save_failure_does_not_update_conversation():
    error = RuntimeError("postgres indisponible")
    service, conversations, messages, rag, _, operations = build_service(
        conversation={"id": CONVERSATION_ID},
        assistant_error=error,
    )

    with pytest.raises(RuntimeError) as raised:
        service.send_message(CONVERSATION_ID, "Question")

    assert raised.value is error
    assert rag.received_kwargs is not None
    assert [message["role"] for message in messages.created] == ["user"]
    assert conversations.updates == []
    assert operations[-1] == ("create_message", "assistant")


def test_no_sources_is_a_successful_persisted_turn():
    service, conversations, messages, _, _, _ = build_service(
        conversation={"id": CONVERSATION_ID},
        rag_response=RAGResponse(
            answer="Information non disponible dans les documents.",
            sources=[],
        ),
    )

    response = service.send_message(CONVERSATION_ID, "Question inconnue")

    assert messages.created[1]["role"] == "assistant"
    assert messages.created[1]["sources"] == []
    assert len(conversations.updates) == 1
    assert response.sources == []
    assert response.answer == "Information non disponible dans les documents."


def test_empty_message_content_becomes_invalid_chat_question():
    class RejectingMessageService(FakeMessageService):
        def create_message(self, **message):
            self.operations.append(("create_message", message["role"]))
            raise EmptyMessageContentError("contenu vide")

    operations = []
    conversations = FakeConversationService(
        conversation={"id": CONVERSATION_ID},
        operations=operations,
    )
    messages = RejectingMessageService(operations=operations)
    rag = FakeRAGPipeline(operations=operations)
    documents = FakeDocumentRepository(operations=operations)
    service = ChatService(rag, conversations, messages, documents)

    with pytest.raises(InvalidChatQuestionError):
        service.send_message(CONVERSATION_ID, "   ")

    assert rag.received_kwargs is None
    assert conversations.updates == []


def test_invalid_message_role_is_not_converted_to_invalid_chat_question():
    class FailingMessageService(FakeMessageService):
        def create_message(self, **message):
            raise InvalidMessageRoleError("rôle invalide")

    conversations = FakeConversationService(
        conversation={"id": CONVERSATION_ID}
    )
    messages = FailingMessageService()
    rag = FakeRAGPipeline()
    service = ChatService(rag, conversations, messages, FakeDocumentRepository())

    with pytest.raises(InvalidMessageRoleError, match="rôle invalide"):
        service.send_message(CONVERSATION_ID, "Question")

    assert rag.received_kwargs is None
