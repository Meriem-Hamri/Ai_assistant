# Configuration du magasin vectoriel
# Implémentation avec ChromaDB

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VectorStoreConfig:
    """
    Configuration du Vector Store.

    Attributes:
        persist_directory:
            Répertoire où ChromaDB stockera les données.

        collection_name:
            Nom de la collection utilisée pour indexer les chunks.

        distance_metric:
            Métrique utilisée pour la recherche vectorielle.
            Valeurs courantes :
            - cosine
            - l2
            - ip
    """

    persist_directory: Path

    collection_name: str

    distance_metric: str = "cosine"