from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentProcessingInput:
    """Données persistées nécessaires au traitement d'un document."""

    id: str
    filename: str
    path: str
    status: str
    title: str | None
    category: str | None
    year: int | None
    person: str | None
    department: str | None
    document_type: str | None
    tags: list[str] | None
