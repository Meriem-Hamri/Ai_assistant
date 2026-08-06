from chromadb import PersistentClient
from chromadb.api.models.Collection import Collection

from app.vectorstore.base import BaseVectorStore
from app.vectorstore.config import VectorStoreConfig
# indexation
from app.vectorstore.utils import prepare_chroma_payload
from app.models.document import Chunk
# Recherche vectorielle
from app.vectorstore.search_result import SearchResult
from app.vectorstore.utils import (
    prepare_chroma_payload,
    build_search_results,
)

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

        "==================================================  GESTION DES COLLECTIONS  ==========/"

        def _delete_collection(self) -> None:
            """
            Supprime la collection ChromaDB.
            """
            self._client.delete_collection(
                name=self._config.collection_name
            )       

        "================================================== Methodes Systemes ==================="
        def count(self) -> int:
            """
            Retourne le nombre de chunks présents
            dans la collection.
            """
            return self._collection.count()

        def clear(self) -> None:
            """
            Supprime tous les chunks de la collection.
            """
            self._delete_collection()
            self._create_collection()

        def close(self) -> None:
            """
            Libère les ressources du Vector Store.

            ChromaDB ne nécessite actuellement
            aucune fermeture explicite.
            """
            return None

        "==================================================== INDEXATION ============"
        def add_chunks(
            self,
            chunks: list[Chunk],
            embeddings: list[list[float]],
        ) -> None:
            """
            Ajoute une liste de chunks dans ChromaDB.

            Args:
                chunks:
                    Chunks à indexer.

                embeddings:
                    Embeddings associés aux chunks.
            """
            if not chunks:
                return

            ids, documents, vectors, metadatas = prepare_chroma_payload(
                chunks,
                embeddings,
            )

            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=vectors,
                metadatas=metadatas,
            )

        def delete_document(
                self,
                document_id: str,
            ) -> None:
                """
                Supprime tous les chunks appartenant à un document.

                Args:
                    document_id:
                        Identifiant du document à supprimer.
                """

                self._collection.delete(
                    where={
                        "document_id": document_id
                    }
                )

        "=================================================== RECHERCHE VECTORIELLE ==========="
        def search(
            self,
            embedding: list[float],
            top_k: int = 5,
        ) -> list[SearchResult]:
            """
            Recherche les chunks les plus pertinents.

            Args:
                embedding:
                    Embedding de la requête.

                top_k:
                    Nombre maximum de résultats.

            Returns:
                Liste des résultats de recherche.
            """

            results = self._collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
            )
            if not results["ids"]:
                return []

            ids = results["ids"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]

            return build_search_results(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                distances=distances,
            )


