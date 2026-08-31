from app.models.document import Chunk
from app.rag.config import RAGConfig
from app.rag.pipeline import RAGPipeline
from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.chroma_store import ChromaStore
from app.vectorstore.config import VectorStoreConfig
from app.llm.qwen_client import QwenClient
from app.prompting.prompt_builder import PromptBuilder
from chromadb import EphemeralClient


def test_rag_end_to_end():

    # ==========================================================
    # 1. Services réels
    # ==========================================================

    embedding_service = EmbeddingService()

    vector_store = ChromaStore(
        VectorStoreConfig(
            host="localhost",
            port=8001,
            collection_name="rag_e2e_collection",
        ),
        client=EphemeralClient(),
    )

    prompt_builder = PromptBuilder()

    llm = QwenClient()

    # ==========================================================
    # 2. Nettoyage de la base de test
    # ==========================================================

    vector_store.clear()

    # ==========================================================
    # 3. Documents / chunks de test
    # ==========================================================

    chunks = [
        Chunk(
            text=(
                "Le contrat de travail est conclu "
                "pour une durée de trois mois."
            ),
            document_id="e2e-doc-1",
            document_name="contrat.pdf",
            page_number=1,
            chunk_index=0,
            start_char=0,
            end_char=65,
        ),
        Chunk(
            text=(
                "Le salarié travaille du lundi au vendredi "
                "de 9h à 17h."
            ),
            document_id="e2e-doc-1",
            document_name="contrat.pdf",
            page_number=2,
            chunk_index=1,
            start_char=0,
            end_char=56,
        ),
        Chunk(
            text=(
                "Le salaire mensuel est fixé "
                "à 8000 dirhams."
            ),
            document_id="e2e-doc-1",
            document_name="contrat.pdf",
            page_number=3,
            chunk_index=2,
            start_char=0,
            end_char=44,
        ),
    ]

    # ==========================================================
    # 4. Embeddings réels
    # ==========================================================

    embeddings = embedding_service.embed_batch(
        [chunk.text for chunk in chunks]
    )

    # ==========================================================
    # 5. Indexation réelle dans ChromaDB
    # ==========================================================

    vector_store.add_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    assert vector_store.count() == 3

    # ==========================================================
    # 6. Pipeline RAG réel
    # ==========================================================

    pipeline = RAGPipeline(
        embedding_service=embedding_service,
        vector_store=vector_store,
        prompt_builder=prompt_builder,
        llm=llm,
        config=RAGConfig(
            top_k=3,
        ),
    )

    # ==========================================================
    # 7. Question utilisateur
    # ==========================================================

    question = "Quelle est la durée du contrat ?"

    # ==========================================================
    # 8. Exécution complète du RAG
    # ==========================================================

    response = pipeline.answer(question)

    # ==========================================================
    # 9. Vérifications
    # ==========================================================

    assert response is not None

    assert response.answer

    print("\n" + "=" * 70)
    print("QUESTION")
    print("=" * 70)
    print(question)

    print("\n" + "=" * 70)
    print("RÉPONSE")
    print("=" * 70)
    print(response.answer)

    print("\n" + "=" * 70)
    print("SOURCES")
    print("=" * 70)

    for source in response.sources:
        print(
            f"- {source.document_name} | "
            f"page={source.page_number} | "
            f"distance={source.distance:.4f}"
        )

    # La source la plus pertinente doit être le contrat,
    # page 1, qui contient la durée.
    assert len(response.sources) > 0

    assert response.sources[0].document_id == "e2e-doc-1"
    assert response.sources[0].page_number == 1

    # Nettoyage
    vector_store.clear()
