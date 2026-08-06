# Objet retourné par une recherche
from dataclasses import dataclass

from app.models.document import Chunk


@dataclass(slots=True)
class SearchResult:
    """
    Représente un résultat retourné par
    une recherche vectorielle.
    """

    chunk: Chunk

    score: float