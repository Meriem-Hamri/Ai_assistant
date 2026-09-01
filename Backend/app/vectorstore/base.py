# Interface abstraite du Vector Store
from abc import ABC, abstractmethod

from app.models.document import Chunk
from app.vectorstore.filters import DocumentFilters
from app.vectorstore.search_result import SearchResult


class BaseVectorStore(ABC):
    """
    Contrat commun à tous les magasins vectoriels.

    Cette interface permet au reste du projet de manipuler
    un Vector Store sans dépendre d'une implémentation
    particulière (ChromaDB, FAISS, Qdrant, etc.).
    """

    @abstractmethod
    def add_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None:
        """Ajoute une liste de chunks et leurs embeddings."""
        ...

    @abstractmethod
    def search(
        self,
        embedding: list[float],
        top_k: int = 5,
        max_distance: float | None = None,
        document_ids: list[str] | tuple[str, ...] | None = None,
        filters: DocumentFilters | None = None,
    ) -> list[SearchResult]:
        """
        Recherche les chunks les plus similaires.

        Args:
            embedding:
                Embedding de la requête.

            top_k:
                Nombre maximum de résultats à retourner.

            max_distance:
                Distance maximale autorisée pour qu'un résultat
                soit considéré comme pertinent.
                Si None, aucun filtrage par distance n'est appliqué.

            document_ids:
                Identifiants des documents à rechercher. None ou une
                collection vide recherche dans tous les documents.

        Returns:
            Liste des résultats de recherche.
        """
        ...

    @abstractmethod
    def delete_document(
        self,
        document_id: str,
    ) -> None:
        """Supprime tous les chunks d'un document."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Retourne le nombre de chunks indexés."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Supprime tous les chunks de la collection."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Libère les ressources éventuelles."""
        ...
