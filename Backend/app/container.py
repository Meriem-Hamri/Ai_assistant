import os
from functools import lru_cache

from app.conversations.repository import ConversationRepository
from app.documents.celery_dispatcher import CeleryDocumentProcessingDispatcher
from app.documents.indexer import DocumentIndexer
from app.documents.processor import DocumentProcessor
from app.documents.repository import DocumentRepository
from app.embeddings.embedding_service import EmbeddingService
from app.llm.qwen_client import QwenClient
from app.metadata.extractor import MetadataExtractor
from app.prompting.prompt_builder import PromptBuilder
from app.rag.config import RAGConfig
from app.rag.pipeline import RAGPipeline
from app.vectorstore.chroma_store import ChromaStore
from app.vectorstore.config import VectorStoreConfig


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


@lru_cache(maxsize=1)
def get_vector_store() -> ChromaStore:
    return ChromaStore(
        config=VectorStoreConfig(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", "8001")),
            collection_name="documents",
        )
    )


@lru_cache(maxsize=1)
def get_document_repository() -> DocumentRepository:
    return DocumentRepository()


@lru_cache(maxsize=1)
def get_document_processing_dispatcher() -> CeleryDocumentProcessingDispatcher:
    return CeleryDocumentProcessingDispatcher()


@lru_cache(maxsize=1)
def get_conversation_repository() -> ConversationRepository:
    return ConversationRepository()


@lru_cache(maxsize=1)
def get_prompt_builder() -> PromptBuilder:
    return PromptBuilder()


@lru_cache(maxsize=1)
def get_llm() -> QwenClient:
    return QwenClient()


@lru_cache(maxsize=1)
def get_metadata_extractor() -> MetadataExtractor:
    return MetadataExtractor()


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RAGPipeline:
    return RAGPipeline(
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store(),
        prompt_builder=get_prompt_builder(),
        llm=get_llm(),
        config=RAGConfig(),
    )


def create_document_processor() -> DocumentProcessor:
    indexer = DocumentIndexer(
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store(),
    )
    return DocumentProcessor(
        indexer=indexer,
        metadata_extractor=get_metadata_extractor(),
    )
