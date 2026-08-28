from pathlib import Path

from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.chroma_store import ChromaStore
from app.vectorstore.config import VectorStoreConfig
from app.documents.repository import DocumentRepository
from app.conversations.repository import ConversationRepository

_embedding_service = EmbeddingService()

_vector_store = ChromaStore(
    config=VectorStoreConfig(
        persist_directory=Path("data/chroma"),
        collection_name="documents",
    )
)

_document_repository = DocumentRepository()

_conversation_repository = ConversationRepository()


def get_embedding_service() -> EmbeddingService:
    return _embedding_service


def get_vector_store() -> ChromaStore:
    return _vector_store

def get_document_repository() -> DocumentRepository:
    return _document_repository

def get_conversation_repository() -> ConversationRepository:
    return _conversation_repository