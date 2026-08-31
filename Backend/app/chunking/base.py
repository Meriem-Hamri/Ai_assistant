from abc import ABC, abstractmethod

from app.models.document import Document, Chunk


class BaseChunker(ABC):
    """
    Interface de base pour tous les chunkers.

    Un chunker est responsable de transformer un document
    en une liste de chunks exploitables par la base vectorielle.
    """

    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]:
        """
        Découpe un document en plusieurs chunks.

        Args:
            document: document à découper.

        Returns:
            Liste des chunks générés.
        """
        pass