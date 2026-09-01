# Configuration du magasin vectoriel
# Implémentation avec ChromaDB

from dataclasses import dataclass


@dataclass(frozen=True)
class VectorStoreConfig:
    """
    Configuration du Vector Store.

    Attributes:
        host:
            Nom d'hôte du serveur ChromaDB.

        port:
            Port HTTP du serveur ChromaDB.

        collection_name:
            Nom de la collection utilisée pour indexer les chunks.

        distance_metric:
            Métrique utilisée pour la recherche vectorielle.
            Valeurs courantes :
            - cosine
            - l2
            - ip
    """

    host: str

    port: int

    collection_name: str

    distance_metric: str = "cosine"
