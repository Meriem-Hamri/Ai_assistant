from app.models.document import Chunk
from app.vectorstore.search_result import SearchResult

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

def build_search_results(
    ids: list[str],
    documents: list[str],
    metadatas: list[dict],
    distances: list[float],
) -> list[SearchResult]:
    """
    Construit les résultats de recherche à partir
    des données retournées par ChromaDB.

    Args:
        ids:
            Identifiants des chunks.

        documents:
            Textes des chunks.

        metadatas:
            Métadonnées des chunks.

        distances:
            Distances retournées par ChromaDB.

    Returns:
        Liste des SearchResult.
    """

    if not (
        len(ids)
        == len(documents)
        == len(metadatas)
        == len(distances)
    ):
        raise ValueError(
            "Les données retournées par ChromaDB sont incohérentes."
        )

    results: list[SearchResult] = []

    for chunk_id, text, metadata, distance in zip(
        ids,
        documents,
        metadatas,
        distances,
    ):
        results.append(
            SearchResult(
                chunk_id=chunk_id,
                text=text,
                score=distance,
                document_id=metadata["document_id"],
                document_name=metadata["document_name"],
                page_number=metadata["page_number"],
                chunk_index=metadata["chunk_index"],
                start_char=metadata["start_char"],
                end_char=metadata["end_char"],
            )
        )

    return results