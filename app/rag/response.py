from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Source:
    """
    Source utilisée pour générer une réponse RAG.
    """

    document_id: str
    document_name: str
    page_number: int
    chunk_id: str
    excerpt: str
    distance: float


@dataclass(frozen=True, slots=True)
class RAGResponse:
    """
    Réponse produite par le pipeline RAG.

    Attributes:
        answer:
            Réponse générée par le LLM.

        sources:
            Sources documentaires utilisées pour construire la réponse.
    """

    answer: str
    sources: list[Source]
