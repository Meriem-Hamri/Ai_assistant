# Interface abstraite du Vector Store
from abc import ABC, abstractmethod

from app.models.document import Chunk
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
    ) -> list[SearchResult]:
        """Recherche les chunks les plus similaires."""
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