from dataclasses import dataclass,field
from typing import Any
from uuid import uuid4

@dataclass #cree une classe qui stocke des données
class DocumentPage:
    """
    Représente une page d'un document
    """
    page_number:int
    text:str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Document:
    """
    Représente un document complet
    """
    filename:str #nom du fichier
    id: str = field(default_factory=lambda: str(uuid4()))
    pages:list[DocumentPage]=field(default_factory=list)#chaque document reçoit sa propre liste vide.
    metadata: dict[str,Any]=field(default_factory=dict)

@dataclass
class Chunk:
    """
    Représente un fragment de document destiné à être indexé
    dans la base vectorielle.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    text: str = ""
    document_id: str = ""
    document_name: str = ""
    page_number: int | None = None
    chunk_index: int = 0
    start_char: int = 0
    end_char: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@property
def source(self) -> str:
    return f"{self.document_name} - page {self.page_number}"

# @dataclass
# class TextSpan:
#     """
#     Représente un fragment du texte original avec
#     ses positions exactes dans la page.
#     """

#     text: str
#     start_char: int
#     end_char: int