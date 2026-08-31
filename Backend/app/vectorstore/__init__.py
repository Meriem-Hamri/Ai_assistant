from app.models.document import Chunk
from app.vectorstore.search_result import SearchResult


def _prepare_business_metadata(metadata: dict) -> dict:
    """Convertit les métadonnées métier au format scalaire de ChromaDB."""

    chroma_metadata: dict = {}

    for key in (
        "title",
        "category",
        "year",
        "person",
        "department",
        "document_type",
    ):
        value = metadata.get(key)
        if value is not None:
            chroma_metadata[key] = value

    tags = metadata.get("tags", [])
    if tags:
        chroma_metadata["tags"] = ", ".join(tags)
        for tag in tags:
            normalized_tag = "".join(
                character.lower()
                if character.isalnum()
                else "_"
                for character in tag
            ).strip("_")
            if normalized_tag:
                chroma_metadata[f"tag_{normalized_tag}"] = True

    return chroma_metadata

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

        metadata = {
            "document_id": chunk.document_id,
            "document_name": chunk.document_name,
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
            "start_char": chunk.start_char,
            "end_char": chunk.end_char,
        }
        metadata.update(_prepare_business_metadata(chunk.metadata))
        metadatas.append(metadata)

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
                distance=distance,
                document_id=metadata["document_id"],
                document_name=metadata["document_name"],
                page_number=metadata["page_number"],
                chunk_index=metadata["chunk_index"],
                start_char=metadata["start_char"],
                end_char=metadata["end_char"],
            )
        )

    return results
