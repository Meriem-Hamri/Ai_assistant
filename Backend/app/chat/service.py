from datetime import datetime, timezone

from app.api.schemas.chat import ChatResponse, ChatSourceResponse
from app.conversations.message_service import (
    EmptyMessageContentError,
    MessageService,
)
from app.conversations.service import ConversationService
from app.rag.pipeline import RAGPipeline
from app.vectorstore.filters import DocumentFilters


class ConversationNotFoundError(Exception):
    """La conversation demandée n'existe pas."""


class InvalidChatQuestionError(Exception):
    """La question ne peut pas être persistée comme message utilisateur."""


class ChatService:
    """
    Service responsable du traitement des questions utilisateur
    via le pipeline RAG.
    """

    def __init__(
        self,
        rag_pipeline: RAGPipeline,
        conversation_service: ConversationService,
        message_service: MessageService,
    ) -> None:
        self._rag_pipeline = rag_pipeline
        self._conversation_service = conversation_service
        self._message_service = message_service

    def send_message(
        self,
        conversation_id: str,
        question: str,
        document_id: str | None = None,
        category: str | None = None,
        year: int | None = None,
        person: str | None = None,
        tags: list[str] | None = None,
        department: str | None = None,
        document_type: str | None = None,
    ) -> ChatResponse:
        conversation = self._conversation_service.get_conversation(
            conversation_id
        )
        if conversation is None:
            raise ConversationNotFoundError

        try:
            persisted_user_message = self._message_service.create_message(
                conversation_id=conversation_id,
                role="user",
                content=question,
                sources=None,
            )
        except EmptyMessageContentError as exc:
            raise InvalidChatQuestionError from exc

        response = self._rag_pipeline.answer(
            question=persisted_user_message["content"],
            document_ids=() if document_id is None else (document_id,),
            filters=DocumentFilters(
                category=category,
                year=year,
                person=person,
                tags=tuple(tags or ()),
                department=department,
                document_type=document_type,
            ),
        )

        source_snapshot = [
            {
                "document_id": source.document_id,
                "document_name": source.document_name,
                "page_number": source.page_number,
                "chunk_id": source.chunk_id,
                "excerpt": source.excerpt,
                "distance": source.distance,
            }
            for source in response.sources
        ]

        self._message_service.create_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response.answer,
            sources=source_snapshot,
        )
        self._conversation_service.update_conversation(
            conversation_id,
            {"updated_at": datetime.now(timezone.utc)},
        )

        return ChatResponse(
            conversation_id=conversation_id,
            answer=response.answer,
            sources=[
                ChatSourceResponse(**source)
                for source in source_snapshot
            ],
        )
