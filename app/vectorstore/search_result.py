# Objet retourné par une recherche
from dataclasses import dataclass

from app.models.document import Chunk


@dataclass(slots=True)
class SearchResult:
    """
    Représente un résultat de recherche vectorielle.
    """

    chunk_id: str

    text: str

    score: float

    document_id: str

    document_name: str

    page_number: int

    chunk_index: int

    start_char: int

    end_char: int