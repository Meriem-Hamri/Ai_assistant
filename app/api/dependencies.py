from pathlib import Path

from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.chroma_store import ChromaStore
from app.vectorstore.config import VectorStoreConfig
from app.documents.repository import DocumentRepository
from app.conversations.repository import ConversationRepository
from app.llm.qwen_client import QwenClient
from app.metadata.extractor import MetadataExtractor
from app.prompting.prompt_builder import PromptBuilder
from app.rag.config import RAGConfig
from app.rag.pipeline import RAGPipeline


_embedding_service = EmbeddingService()

_vector_store = ChromaStore(
    config=VectorStoreConfig(
        persist_directory=Path("data/chroma"),
        collection_name="documents",
    )
)

_document_repository = DocumentRepository()

_conversation_repository = ConversationRepository()

_prompt_builder = PromptBuilder()
_llm = QwenClient()
_metadata_extractor = MetadataExtractor()
_rag_pipeline = RAGPipeline(
    embedding_service=_embedding_service,
    vector_store=_vector_store,
    prompt_builder=_prompt_builder,
    llm=_llm,
    config=RAGConfig(),
)


def get_embedding_service() -> EmbeddingService:
    return _embedding_service


def get_vector_store() -> ChromaStore:
    return _vector_store

def get_document_repository() -> DocumentRepository:
    return _document_repository

def get_conversation_repository() -> ConversationRepository:
    return _conversation_repository

def get_rag_pipeline() -> RAGPipeline:
    return _rag_pipeline


def get_metadata_extractor() -> MetadataExtractor:
    return _metadata_extractor
