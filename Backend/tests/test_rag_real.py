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


PDF_PATH = Path(
    "documents/pdf/DOCUMENT_DE_TEST_ASSISTANT_RAG.pdf"
)

DB_PATH = Path("data/test_real_rag")


def create_pipeline():
    # --------------------------------------------------
    # 1. Extraction
    # --------------------------------------------------

    document = extract_document(str(PDF_PATH))

    print("\n" + "=" * 70)
    print("DOCUMENT")
    print("=" * 70)
    print(f"Nom : {document.filename}")
    print(f"Pages : {len(document.pages)}")

    # --------------------------------------------------
    # 2. Cleaning
    # --------------------------------------------------

    for page in document.pages:
        page.text = clean_document(page.text)

    # --------------------------------------------------
    # 3. Chunking
    # --------------------------------------------------

    chunker = NaturalChunker()

    chunks = chunker.chunk(document)

    print(f"Chunks créés : {len(chunks)}")

    # --------------------------------------------------
    # 4. Embeddings
    # --------------------------------------------------

    embedding_service = EmbeddingService()

    embeddings = embedding_service.embed_batch(
        [chunk.text for chunk in chunks]
    )

    print(f"Embeddings créés : {len(embeddings)}")

    # --------------------------------------------------
    # 5. ChromaDB
    # --------------------------------------------------

    config = VectorStoreConfig(
        persist_directory=DB_PATH,
        collection_name="real_rag_test",
    )

    store = ChromaStore(config)

    # On nettoie la collection avant le test
    store.clear()

    store.add_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    print("Chunks indexés dans ChromaDB.")

    # --------------------------------------------------
    # 6. Prompt Builder
    # --------------------------------------------------

    prompt_builder = PromptBuilder()

    # --------------------------------------------------
    # 7. LLM local
    # --------------------------------------------------

    llm = QwenClient()

    # --------------------------------------------------
    # 8. RAG Pipeline
    # --------------------------------------------------

    rag_config = RAGConfig(
        top_k=3
    )

    pipeline = RAGPipeline(
        embedding_service=embedding_service,
        vector_store=store,
        prompt_builder=prompt_builder,
        llm=llm,
        config=rag_config,
    )

    return pipeline


def main():
    if not PDF_PATH.exists():
        print(
            f"ERREUR : fichier introuvable : {PDF_PATH}"
        )
        return

    pipeline = create_pipeline()

    print("\n" + "=" * 70)
    print("ASSISTANT RAG — TEST RÉEL")
    print("=" * 70)
    print("Le document a été chargé et indexé.")
    print("Pose tes questions.")
    print("Tape 'quit' pour quitter.")
    print("=" * 70)

    while True:

        question = input("\nQuestion : ").strip()

        if question.lower() in {"quit", "exit", "q"}:
            print("\nFin du test.")
            break

        if not question:
            continue

        try:
            response = pipeline.answer(question)

            print("\n" + "-" * 70)
            print("RÉPONSE")
            print("-" * 70)
            print(response.answer)

            print("\n" + "-" * 70)
            print("SOURCES")
            print("-" * 70)

            if response.sources:
                for source in response.sources:
                    print(
                        f"- {source.document_name} | "
                        f"page={source.page_number} | "
                        f"distance={source.distance:.4f}"
                    )
            else:
                print("Aucune source.")

        except Exception as exc:
            print("\nERREUR :")
            print(exc)


if __name__ == "__main__":
    main()