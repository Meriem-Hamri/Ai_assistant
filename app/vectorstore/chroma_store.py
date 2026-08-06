from chromadb import PersistentClient
from chromadb.api.models.Collection import Collection

from app.vectorstore.base import BaseVectorStore
from app.vectorstore.config import VectorStoreConfig

class ChromaStore(BaseVectorStore):
    """
    Implémentation du Vector Store utilisant ChromaDB.
    """
    def __init__(self, config: VectorStoreConfig) -> None:
        """
        Initialise le Vector Store.

        Args:
            config: Configuration du Vector Store.
        """
        self._config = config

        self._create_client()
        self._create_collection()

    def _create_client(self) -> None:
        """
        Crée le client ChromaDB.
        """
        self._config.persist_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._client = PersistentClient(
            path=str(self._config.persist_directory)
        )

    def _create_collection(self) -> None:
        """
        Ouvre ou crée la collection ChromaDB.
        """
        self._collection: Collection = (
            self._client.get_or_create_collection(
                name=self._config.collection_name,
                metadata={
                    "hnsw:space": self._config.distance_metric
                },
            )
        )

        "============  GESTION DES COLLECTIONS  ==========/"
        
