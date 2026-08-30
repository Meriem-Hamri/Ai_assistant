from app.embeddings.embedding_service import EmbeddingService
from app.models.document import Chunk


def test_measure_retrieval_distances(store):
    embedding_service = EmbeddingService()

    chunks = [
        Chunk(
            text=(
                "Le contrat de travail est conclu "
                "pour une durée de trois mois."
            ),
            document_id="doc1",
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
            document_id="doc1",
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
            document_id="doc1",
            document_name="contrat.pdf",
            page_number=3,
            chunk_index=2,
            start_char=0,
            end_char=44,
        ),
        Chunk(
            text=(
                "Les congés annuels sont de "
                "vingt-deux jours ouvrables."
            ),
            document_id="doc1",
            document_name="contrat.pdf",
            page_number=4,
            chunk_index=3,
            start_char=0,
            end_char=55,
        ),
    ]

    embeddings = embedding_service.embed_batch(
        [chunk.text for chunk in chunks]
    )

    store.add_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    questions = [
        "Quelle est la durée du contrat ?",
        "Combien de mois dure le contrat ?",
        "Quel est le salaire mensuel ?",
        "Combien de jours de congé sont prévus ?",
        "Quelle est la capitale de l'Espagne ?",
    ]

    for question in questions:
        query_embedding = embedding_service.embed(question)

        results = store.search(
            embedding=query_embedding,
            top_k=4,
        )

        print("\n" + "=" * 70)
        print(f"QUESTION : {question}")
        print("=" * 70)

        for index, result in enumerate(results, start=1):
            print(
                f"{index}. "
                f"distance={result.distance:.4f} | "
                f"page={result.page_number}"
            )
            print(f"   {result.text}")