import inspect
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select

from app.conversations.repository import ConversationRepository
from app.database.models import ConversationModel, DocumentModel, MessageModel
from app.database.session import SessionLocal


def build_conversation(**overrides) -> dict:
    conversation = {
        "id": str(uuid4()),
        "title": "Conversation de test",
        "active_document_id": None,
    }
    conversation.update(overrides)
    return conversation


def cleanup(*conversation_ids: str, document_ids: tuple[str, ...] = ()) -> None:
    with SessionLocal() as session:
        for conversation_id in conversation_ids:
            conversation = session.get(ConversationModel, UUID(conversation_id))
            if conversation is not None:
                session.delete(conversation)
        for document_id in document_ids:
            document = session.get(DocumentModel, UUID(document_id))
            if document is not None:
                session.delete(document)
        session.commit()


def test_save_and_get_by_id_return_persisted_contract():
    repository = ConversationRepository()
    data = build_conversation()

    try:
        saved = repository.save(data)
        fetched = repository.get_by_id(data["id"])

        assert saved == fetched
        assert set(saved) == {
            "id",
            "title",
            "active_document_id",
            "created_at",
            "updated_at",
        }
        assert saved["id"] == data["id"]
        assert saved["title"] == data["title"]
        assert saved["active_document_id"] is None
        assert saved["created_at"] is not None
        assert saved["updated_at"] is not None
        assert repository.get_by_id("identifiant-invalide") is None
        assert repository.get_by_id(str(uuid4())) is None
    finally:
        cleanup(data["id"])


def test_get_all_orders_by_updated_at_descending():
    repository = ConversationRepository()
    now = datetime.now(timezone.utc)
    older = build_conversation(
        title="Ancienne",
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=1),
    )
    newer = build_conversation(
        title="Récente",
        created_at=now - timedelta(days=1),
        updated_at=now,
    )

    try:
        repository.save(older)
        repository.save(newer)

        positions = {
            item["id"]: index
            for index, item in enumerate(repository.get_all())
            if item["id"] in {older["id"], newer["id"]}
        }
        assert positions[newer["id"]] < positions[older["id"]]
    finally:
        cleanup(older["id"], newer["id"])


def test_update_title_active_document_and_ignore_forbidden_fields():
    repository = ConversationRepository()
    conversation = build_conversation()
    document_id = str(uuid4())
    original_created_at = datetime.now(timezone.utc) - timedelta(days=10)
    conversation["created_at"] = original_created_at

    with SessionLocal() as session:
        session.add(
            DocumentModel(
                id=UUID(document_id),
                filename=f"{document_id}.pdf",
                type="pdf",
                size=1,
                path=f"documents/{document_id}.pdf",
                status="ready",
            )
        )
        session.commit()

    try:
        repository.save(conversation)
        replacement_id = str(uuid4())
        result = repository.update(
            conversation["id"],
            {
                "title": "Titre modifié",
                "active_document_id": document_id,
                "id": replacement_id,
                "created_at": datetime.now(timezone.utc),
            },
        )

        assert result is not None
        assert result["title"] == "Titre modifié"
        assert result["active_document_id"] == document_id
        assert result["id"] == conversation["id"]
        assert result["created_at"] == original_created_at
        assert repository.get_by_id(replacement_id) is None
        assert repository.update("invalide", {"title": "x"}) is None
        assert repository.update(str(uuid4()), {"title": "x"}) is None
    finally:
        cleanup(conversation["id"], document_ids=(document_id,))


def test_delete_and_invalid_id():
    repository = ConversationRepository()
    conversation = build_conversation()

    try:
        repository.save(conversation)
        assert repository.delete(conversation["id"]) is True
        assert repository.get_by_id(conversation["id"]) is None
        assert repository.delete(conversation["id"]) is False
        assert repository.delete("invalide") is False
    finally:
        cleanup(conversation["id"])


def test_delete_conversation_cascades_to_messages():
    repository = ConversationRepository()
    conversation = build_conversation()
    message_id = uuid4()

    try:
        repository.save(conversation)
        with SessionLocal() as session:
            session.add(
                MessageModel(
                    id=message_id,
                    conversation_id=UUID(conversation["id"]),
                    role="user",
                    content="Question",
                )
            )
            session.commit()

        assert repository.delete(conversation["id"]) is True
        with SessionLocal() as session:
            assert session.get(MessageModel, message_id) is None
    finally:
        with SessionLocal() as session:
            messages = session.scalars(
                select(MessageModel).where(MessageModel.id == message_id)
            ).all()
            for message in messages:
                session.delete(message)
            session.commit()
        cleanup(conversation["id"])


def test_repository_has_no_json_storage_dependency():
    source = inspect.getsource(ConversationRepository)

    assert "conversations.json" not in source
    assert "json" not in source
    assert "Path" not in source
