from datetime import datetime, timezone

from app.api.schemas.chat import ChatResponse, ChatSourceResponse
from app.conversations.message_service import (
    EmptyMessageContentError,
    MessageService,
    normalize_document_ids,
)
from app.conversations.service import ConversationService
from app.documents.repository import DocumentRepository
from app.rag.pipeline import RAGPipeline
from app.vectorstore.filters import DocumentFilters


class ConversationNotFoundError(Exception):
    """La conversation demandée n'existe pas."""


class InvalidChatQuestionError(Exception):
    """La question ne peut pas être persistée comme message utilisateur."""


class ChatDocumentNotFoundError(Exception):
    """Au moins un document sélectionné n'existe pas."""


class ChatDocumentNotReadyError(Exception):
    """Au moins un document sélectionné n'est pas prêt."""


class ChatService:
    """
    Service responsable du traitement des questions utilisateur
    via le pipeline RAG.
    """

    _MAX_HISTORY_MESSAGES = 6

    def __init__(
        self,
        rag_pipeline: RAGPipeline,
        conversation_service: ConversationService,
        message_service: MessageService,
        document_repository: DocumentRepository,
    ) -> None:
        self._rag_pipeline = rag_pipeline
        self._conversation_service = conversation_service
        self._message_service = message_service
        self._document_repository = document_repository

    def send_message(
        self,
        conversation_id: str,
        question: str,
        document_ids: list[str] | tuple[str, ...] | None = None,
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

        normalized_document_ids = normalize_document_ids(document_ids)
        if normalized_document_ids:
            documents = self._document_repository.get_by_ids(
                normalized_document_ids
            )
            documents_by_id = {
                document["id"]: document for document in documents
            }
            if any(
                document_id not in documents_by_id
                for document_id in normalized_document_ids
            ):
                raise ChatDocumentNotFoundError
            if any(
                documents_by_id[document_id]["status"] != "ready"
                for document_id in normalized_document_ids
            ):
                raise ChatDocumentNotReadyError

        existing_messages = self._message_service.get_messages(
            conversation_id
        )
        conversation_history = [
            {
                "role": message["role"],
                "content": message["content"],
            }
            for message in existing_messages[-self._MAX_HISTORY_MESSAGES:]
        ]

        try:
            persisted_user_message = self._message_service.create_message(
                conversation_id=conversation_id,
                role="user",
                content=question,
                sources=None,
                document_ids=normalized_document_ids,
            )
        except EmptyMessageContentError as exc:
            raise InvalidChatQuestionError from exc

        response = self._rag_pipeline.answer(
            question=persisted_user_message["content"],
            document_ids=tuple(normalized_document_ids),
            filters=DocumentFilters(
                category=category,
                year=year,
                person=person,
                tags=tuple(tags or ()),
                department=department,
                document_type=document_type,
            ),
            conversation_history=conversation_history,
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
            document_ids=[],
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
