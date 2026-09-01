from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.conversations.message_repository import MessageRepository
from app.conversations.repository import ConversationRepository
from app.database.models import ConversationModel
from app.database.session import SessionLocal


def create_conversation(repository: ConversationRepository) -> str:
    conversation_id = str(uuid4())
    repository.save(
        {
            "id": conversation_id,
            "title": f"Conversation {conversation_id}",
        }
    )
    return conversation_id


def cleanup(*conversation_ids: str) -> None:
    with SessionLocal() as session:
        for conversation_id in conversation_ids:
            conversation = session.get(ConversationModel, UUID(conversation_id))
            if conversation is not None:
                session.delete(conversation)
        session.commit()


def test_save_user_and_assistant_with_sources_then_get_by_id():
    conversations = ConversationRepository()
    messages = MessageRepository()
    conversation_id = create_conversation(conversations)
    user = {
        "id": str(uuid4()),
        "conversation_id": conversation_id,
        "role": "user",
        "content": "Question",
        "sources": None,
    }
    sources = [{"document_id": str(uuid4()), "excerpt": "Source"}]
    assistant = {
        "id": str(uuid4()),
        "conversation_id": conversation_id,
        "role": "assistant",
        "content": "Réponse",
        "sources": sources,
    }

    try:
        saved_user = messages.save(user)
        saved_assistant = messages.save(assistant)

        assert saved_user["role"] == "user"
        assert saved_user["sources"] is None
        assert saved_user["document_ids"] == []
        assert saved_assistant["role"] == "assistant"
        assert saved_assistant["sources"] == sources
        assert saved_assistant["document_ids"] == []
        assert saved_assistant["created_at"] is not None
        assert messages.get_by_id(assistant["id"]) == saved_assistant
        assert messages.get_by_id("invalide") is None
        assert messages.get_by_id(str(uuid4())) is None
    finally:
        cleanup(conversation_id)


def test_get_by_conversation_is_isolated_and_ordered_by_date_then_id():
    conversations = ConversationRepository()
    messages = MessageRepository()
    first_conversation_id = create_conversation(conversations)
    second_conversation_id = create_conversation(conversations)
    base_time = datetime.now(timezone.utc)
    lower_id = "00000000-0000-0000-0000-000000000001"
    higher_id = "00000000-0000-0000-0000-000000000002"
    older_id = str(uuid4())

    try:
        messages.save(
            {
                "id": higher_id,
                "conversation_id": first_conversation_id,
                "role": "assistant",
                "content": "Même date, second UUID",
                "created_at": base_time,
            }
        )
        messages.save(
            {
                "id": older_id,
                "conversation_id": first_conversation_id,
                "role": "user",
                "content": "Plus ancien",
                "created_at": base_time - timedelta(seconds=1),
            }
        )
        messages.save(
            {
                "id": lower_id,
                "conversation_id": first_conversation_id,
                "role": "assistant",
                "content": "Même date, premier UUID",
                "created_at": base_time,
            }
        )
        isolated_id = str(uuid4())
        messages.save(
            {
                "id": isolated_id,
                "conversation_id": second_conversation_id,
                "role": "user",
                "content": "Autre conversation",
            }
        )

        first_messages = messages.get_by_conversation(first_conversation_id)
        assert [message["id"] for message in first_messages] == [
            older_id,
            lower_id,
            higher_id,
        ]
        assert all(
            message["conversation_id"] == first_conversation_id
            for message in first_messages
        )
        assert [
            message["id"]
            for message in messages.get_by_conversation(second_conversation_id)
        ] == [isolated_id]
        assert messages.get_by_conversation("invalide") == []
        assert messages.get_by_conversation(str(uuid4())) == []
    finally:
        cleanup(first_conversation_id, second_conversation_id)
