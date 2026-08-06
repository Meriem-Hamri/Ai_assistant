from app.models.document import Chunk


def prepare_chroma_payload(
    chunks: list[Chunk],
    embeddings: list[list[float]],
) -> tuple[
    list[str],
    list[str],
    list[list[float]],
    list[dict],
]:
    """
    Prépare les données au format attendu par ChromaDB.

    Args:
        chunks:
            Liste des chunks à indexer.

        embeddings:
            Embeddings associés aux chunks.

    Returns:
        Un tuple contenant :
        - ids
        - documents
        - embeddings
        - metadatas

    Raises:
        ValueError:
            Si le nombre de chunks et d'embeddings est différent.
    """

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Le nombre de chunks et d'embeddings doit être identique."
        )

    ids: list[str] = []
    documents: list[str] = []
    vectors: list[list[float]] = []
    metadatas: list[dict] = []

    for chunk, embedding in zip(chunks, embeddings):

        ids.append(chunk.id)
        documents.append(chunk.text)
        vectors.append(embedding)

        metadatas.append(
            {
                "document_id": chunk.document_id,
                "document_name": chunk.document_name,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
            }
        )

    return ids, documents, vectors, metadatas