from pathlib import Path

from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.chroma_store import ChromaStore
from app.vectorstore.config import VectorStoreConfig


_embedding_service = EmbeddingService()

_vector_store = ChromaStore(
    config=VectorStoreConfig(
        persist_directory=Path("data/chroma"),
        collection_name="documents",
    )
)


def get_embedding_service() -> EmbeddingService:
    return _embedding_service


def get_vector_store() -> ChromaStore:
    return _vector_store