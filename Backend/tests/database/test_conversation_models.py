import uuid

from sqlalchemy import inspect, select

from app.database.models import (
    ConversationModel,
    DocumentModel,
    MessageModel,
)
from app.database.session import SessionLocal


def test_conversation_and_message_mappings():
    conversation_table = ConversationModel.__table__
    message_table = MessageModel.__table__

    active_document_fk = next(
        iter(conversation_table.c.active_document_id.foreign_keys)
    )
    conversation_fk = next(
        iter(message_table.c.conversation_id.foreign_keys)
    )

    assert active_document_fk.target_fullname == "documents.id"
    assert active_document_fk.ondelete == "SET NULL"
    assert conversation_fk.target_fullname == "conversations.id"
    assert conversation_fk.ondelete == "CASCADE"
    assert conversation_table.c.active_document_id.nullable is True
    assert message_table.c.sources.nullable is True
    assert conversation_table.c.created_at.type.timezone is True
    assert conversation_table.c.updated_at.type.timezone is True
    assert message_table.c.created_at.type.timezone is True
    assert conversation_table.c.updated_at.index is True
    assert message_table.c.conversation_id.index is True

    conversation_relationship = inspect(
        ConversationModel
    ).relationships.messages
    message_relationship = inspect(MessageModel).relationships.conversation

    assert conversation_relationship.back_populates == "conversation"
    assert conversation_relationship.passive_deletes is True
    assert conversation_relationship.cascade.delete_orphan is True
    assert message_relationship.back_populates == "messages"


def test_conversation_message_sources_and_delete_cascade():
    conversation_id = uuid.uuid4()
    message_id = uuid.uuid4()
    sources = [
        {
            "document_id": str(uuid.uuid4()),
            "document_name": "guide.pdf",
            "page_number": 2,
            "chunk_id": "chunk-1",
            "excerpt": "Extrait de test",
            "distance": 0.12,
        }
    ]

    try:
        with SessionLocal() as session:
            conversation = ConversationModel(
                id=conversation_id,
                title="Conversation de test",
            )
            message = MessageModel(
                id=message_id,
                role="assistant",
                content="Réponse de test",
                sources=sources,
            )
            conversation.messages.append(message)
            session.add(conversation)
            session.commit()

        with SessionLocal() as session:
            persisted_conversation = session.get(
                ConversationModel,
                conversation_id,
            )
            persisted_message = session.get(MessageModel, message_id)

            assert persisted_conversation is not None
            assert persisted_conversation.active_document_id is None
            assert persisted_message is not None
            assert persisted_message.conversation_id == conversation_id
            assert persisted_message.conversation.id == conversation_id
            assert persisted_message.sources == sources

        with SessionLocal() as session:
            persisted_conversation = session.get(
                ConversationModel,
                conversation_id,
            )
            assert persisted_conversation is not None
            session.delete(persisted_conversation)
            session.commit()

        with SessionLocal() as session:
            assert session.get(MessageModel, message_id) is None
    finally:
        with SessionLocal() as session:
            messages = session.scalars(
                select(MessageModel).where(
                    MessageModel.id == message_id
                )
            ).all()
            for message in messages:
                session.delete(message)

            conversation = session.get(
                ConversationModel,
                conversation_id,
            )
            if conversation is not None:
                session.delete(conversation)
            session.commit()


def test_deleting_document_clears_active_document_id():
    document_id = uuid.uuid4()
    conversation_id = uuid.uuid4()

    try:
        with SessionLocal() as session:
            document = DocumentModel(
                id=document_id,
                filename="active-document.pdf",
                type="pdf",
                size=123,
                path=f"documents/{document_id}.pdf",
                status="ready",
            )
            conversation = ConversationModel(
                id=conversation_id,
                title="Conversation avec document",
                active_document_id=document_id,
            )
            session.add(document)
            session.flush()
            session.add(conversation)
            session.commit()

        with SessionLocal() as session:
            document = session.get(DocumentModel, document_id)
            assert document is not None
            session.delete(document)
            session.commit()

        with SessionLocal() as session:
            conversation = session.get(
                ConversationModel,
                conversation_id,
            )
            assert conversation is not None
            assert conversation.active_document_id is None
    finally:
        with SessionLocal() as session:
            conversation = session.get(
                ConversationModel,
                conversation_id,
            )
            if conversation is not None:
                session.delete(conversation)

            document = session.get(DocumentModel, document_id)
            if document is not None:
                session.delete(document)
            session.commit()
