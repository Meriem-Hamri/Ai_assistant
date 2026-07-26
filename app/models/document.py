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
    id: str
    text: str
    page_number: int
    document_name: str