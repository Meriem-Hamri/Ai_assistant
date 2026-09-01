from typing import Protocol


class DocumentProcessingDispatcher(Protocol):
    """Publie une demande de traitement pour un document persisté."""

    def enqueue(self, document_id: str) -> None:
        """Planifie le traitement du document identifié."""
