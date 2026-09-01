from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.conversations.message_repository import MessageRepository
from app.conversations.message_service import MessageService
from app.conversations.repository import ConversationRepository
from app.database.models import (
    ConversationModel,
    DocumentModel,
    MessageDocumentModel,
    MessageModel,
)
from app.database.session import SessionLocal


def create_conversation() -> str:
    conversation_id = str(uuid4())
    ConversationRepository().save(
        {
            "id": conversation_id,
            "title": f"Conversation {conversation_id}",
        }
    )
    return conversation_id


def create_document() -> str:
    document_id = str(uuid4())
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
    return document_id


def cleanup(
    *conversation_ids: str,
    document_ids: tuple[str, ...] = (),
) -> None:
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


def save_message(
    conversation_id: str,
    document_ids: list[str],
    *,
    message_id: str | None = None,
    created_at: datetime | None = None,
) -> str:
    message_id = message_id or str(uuid4())
    data = {
        "id": message_id,
        "conversation_id": conversation_id,
        "role": "user",
        "content": "Question",
        "document_ids": document_ids,
    }
    if created_at is not None:
        data["created_at"] = created_at
    MessageRepository().save(data)
    return message_id


def test_save_multiple_documents_preserves_positions_and_read_order():
    conversation_id = create_conversation()
    document_ids = tuple(create_document() for _ in range(3))
    ordered_document_ids = [document_ids[0], document_ids[2], document_ids[1]]
    message_id = str(uuid4())

    try:
        saved = MessageRepository().save(
            {
                "id": message_id,
                "conversation_id": conversation_id,
                "role": "user",
                "content": "Question multi-document",
                "document_ids": ordered_document_ids,
            }
        )

        assert saved["document_ids"] == ordered_document_ids
        assert MessageRepository().get_by_id(message_id)["document_ids"] == (
            ordered_document_ids
        )
        with SessionLocal() as session:
            links = session.scalars(
                select(MessageDocumentModel)
                .where(MessageDocumentModel.message_id == UUID(message_id))
                .order_by(MessageDocumentModel.position)
            ).all()
            assert [str(link.document_id) for link in links] == ordered_document_ids
            assert [link.position for link in links] == [0, 1, 2]
    finally:
        cleanup(conversation_id, document_ids=document_ids)


def test_service_normalization_persists_duplicate_document_once():
    conversation_id = create_conversation()
    document_id = create_document()

    try:
        saved = MessageService(MessageRepository()).create_message(
            conversation_id,
            "user",
            "Question",
            document_ids=[f" {document_id} ", document_id],
        )

        assert saved["document_ids"] == [document_id]
        with SessionLocal() as session:
            assert session.scalar(
                select(func.count())
                .select_from(MessageDocumentModel)
                .where(MessageDocumentModel.message_id == UUID(saved["id"]))
            ) == 1
    finally:
        cleanup(conversation_id, document_ids=(document_id,))


def test_get_by_conversation_keeps_message_and_document_order():
    conversation_id = create_conversation()
    document_ids = (create_document(), create_document())
    base_time = datetime.now(timezone.utc)
    lower_id = "00000000-0000-0000-0000-000000000001"
    higher_id = "00000000-0000-0000-0000-000000000002"
    older_id = str(uuid4())

    try:
        save_message(
            conversation_id,
            [document_ids[1], document_ids[0]],
            message_id=higher_id,
            created_at=base_time,
        )
        save_message(
            conversation_id,
            [],
            message_id=older_id,
            created_at=base_time - timedelta(seconds=1),
        )
        save_message(
            conversation_id,
            [document_ids[0]],
            message_id=lower_id,
            created_at=base_time,
        )

        results = MessageRepository().get_by_conversation(conversation_id)
        assert [result["id"] for result in results] == [
            older_id,
            lower_id,
            higher_id,
        ]
        assert results[0]["document_ids"] == []
        assert results[1]["document_ids"] == [document_ids[0]]
        assert results[2]["document_ids"] == [
            document_ids[1],
            document_ids[0],
        ]
    finally:
        cleanup(conversation_id, document_ids=document_ids)


def test_deleting_message_cascades_to_document_links():
    conversation_id = create_conversation()
    document_id = create_document()
    message_id = save_message(conversation_id, [document_id])

    try:
        with SessionLocal() as session:
            message = session.get(MessageModel, UUID(message_id))
            assert message is not None
            session.delete(message)
            session.commit()
        with SessionLocal() as session:
            assert session.get(
                MessageDocumentModel,
                (UUID(message_id), UUID(document_id)),
            ) is None
    finally:
        cleanup(conversation_id, document_ids=(document_id,))


def test_deleting_document_keeps_message_and_other_link():
    conversation_id = create_conversation()
    first_document_id = create_document()
    second_document_id = create_document()
    message_id = str(uuid4())
    sources = [{"document_id": first_document_id, "excerpt": "Historique"}]
    MessageRepository().save(
        {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": "Réponse",
            "sources": sources,
            "document_ids": [first_document_id, second_document_id],
        }
    )

    try:
        with SessionLocal() as session:
            document = session.get(DocumentModel, UUID(first_document_id))
            assert document is not None
            session.delete(document)
            session.commit()

        persisted = MessageRepository().get_by_id(message_id)
        assert persisted is not None
        assert persisted["document_ids"] == [second_document_id]
        assert persisted["sources"] == sources
    finally:
        cleanup(
            conversation_id,
            document_ids=(first_document_id, second_document_id),
        )


def test_deleting_conversation_cascades_transitively():
    conversation_id = create_conversation()
    document_id = create_document()
    message_id = save_message(conversation_id, [document_id])

    try:
        assert ConversationRepository().delete(conversation_id) is True
        with SessionLocal() as session:
            assert session.get(MessageModel, UUID(message_id)) is None
            assert session.get(
                MessageDocumentModel,
                (UUID(message_id), UUID(document_id)),
            ) is None
    finally:
        cleanup(conversation_id, document_ids=(document_id,))


def test_save_rolls_back_message_when_document_fk_is_invalid():
    conversation_id = create_conversation()
    message_id = str(uuid4())

    try:
        with pytest.raises(IntegrityError):
            save_message(conversation_id, [str(uuid4())], message_id=message_id)

        with SessionLocal() as session:
            assert session.get(MessageModel, UUID(message_id)) is None
            assert session.scalar(
                select(func.count())
                .select_from(MessageDocumentModel)
                .where(MessageDocumentModel.message_id == UUID(message_id))
            ) == 0
    finally:
        cleanup(conversation_id)
