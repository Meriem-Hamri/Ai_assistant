from pathlib import Path

from app.extraction.extraction_service import extract_document
from app.cleaning.cleaner import clean_document
from app.chunking.natural_chunker import NaturalChunker
from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.chroma_store import ChromaStore
from app.vectorstore.config import VectorStoreConfig
from app.prompting.prompt_builder import PromptBuilder
from app.llm.qwen_client import QwenClient
from app.rag.config import RAGConfig
from app.rag.pipeline import RAGPipeline
import tempfile
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENT_PATH = (
    "documents/pdf/DOCUMENT_DE_TEST_ASSISTANT_RAG.pdf"
)

TEST_DB = "test_chroma_real"


# ============================================================
# PREPARATION DU DOCUMENT
# ============================================================

def prepare_document(file_path: str):
    """
    Extrait et nettoie automatiquement le document.

    La détection du type de document est entièrement gérée
    par extraction_service.py.
    """

    document = extract_document(file_path)

    for page in document.pages:
        page.text = clean_document(page.text)

    return document


# ============================================================
# CREATION DU PIPELINE
# ============================================================

def create_pipeline():
    embedding_service = EmbeddingService()

    vector_store_config = VectorStoreConfig(
        persist_directory=Path("data/chroma_db"),
        collection_name="test_documents",
    )

    vector_store = ChromaStore(
        vector_store_config
    )

    vector_store.clear()

    prompt_builder = PromptBuilder()

    llm = QwenClient()

    rag_config = RAGConfig(
        top_k=3
    )

    pipeline = RAGPipeline(
        embedding_service=embedding_service,
        vector_store=vector_store,
        prompt_builder=prompt_builder,
        llm=llm,
        config=rag_config,
    )

    return (
        pipeline,
        embedding_service,
        vector_store,
    )


# ============================================================
# INDEXATION DU DOCUMENT
# ============================================================

def index_document(
    document,
    embedding_service,
    vector_store,
):
    """
    Prépare et indexe un document dans ChromaDB.
    """

    chunker = NaturalChunker()

    chunks = chunker.chunk(document)

    print(f"Chunks créés : {len(chunks)}")

    embeddings = embedding_service.embed_batch(
        [chunk.text for chunk in chunks]
    )

    print(
        f"Embeddings créés : {len(embeddings)}"
    )

    vector_store.add_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    print("Chunks indexés dans ChromaDB.")

    return chunks


# ============================================================
# TEST REEL INTERACTIF
# ============================================================

def main():

    file_path = input(
        "Chemin du document : "
    ).strip()

    document = prepare_document(file_path)

    print("\nDOCUMENT")
    print("=" * 70)
    print(f"Nom : {document.filename}")
    print(f"Pages : {len(document.pages)}")

    pipeline, embedding_service, vector_store = (
        create_pipeline()
    )

    index_document(
        document=document,
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    print("\nASSISTANT RAG — TEST RÉEL")
    print("=" * 70)
    print("Le document a été chargé et indexé.")
    print("Pose tes questions.")
    print("Tape 'quit' pour quitter.")
    print("=" * 70)

    while True:

        question = input("\nQuestion : ").strip()

        if question.lower() == "quit":
            break

        response = pipeline.answer(question)

        print("\n" + "-" * 70)
        print("RÉPONSE")
        print("-" * 70)
        print(response.answer)

        print("\nSOURCES")
        print("-" * 70)

        for source in response.sources:
            print(
                f"- {source.document_name} "
                f"| page={source.page_number} "
                f"| distance={source.distance:.4f}"
            )


if __name__ == "__main__":
    main()
