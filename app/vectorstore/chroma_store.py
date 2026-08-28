from chromadb import PersistentClient
from chromadb.api.models.Collection import Collection

from app.vectorstore.base import BaseVectorStore
from app.vectorstore.config import VectorStoreConfig
# indexation
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
            Libère les ressources utilisées par le Vector Store.
            """

            self._collection = None
            self._client = None

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
            max_distance: float | None = None,
            document_id: str | None = None,
        ) -> list[SearchResult]:
            """
            Recherche les chunks les plus pertinents.

            Args:
                embedding:
                    Embedding de la requête.

                top_k:
                    Nombre maximum de résultats à retourner.

                max_distance:
                    Distance maximale autorisée pour un résultat.
                    Si None, aucun filtrage par distance n'est appliqué.

            Returns:
                Liste des résultats de recherche triés par distance
                croissante, le résultat le plus proche étant en premier.

            Raises:
                ValueError:
                    Si l'embedding est vide, si top_k n'est pas positif
                    ou si max_distance est négatif.

                TypeError:
                    Si top_k ou max_distance possède un type invalide.
            """

            if embedding is None or len(embedding) == 0:
                raise ValueError(
                    "L'embedding de recherche ne peut pas être vide."
                )

            if not isinstance(top_k, int) or isinstance(top_k, bool):
                raise TypeError(
                    "top_k doit être un entier."
                )

            if top_k <= 0:
                raise ValueError(
                    "top_k doit être strictement positif."
                )

            if max_distance is not None:
                if (
                    isinstance(max_distance, bool)
                    or not isinstance(max_distance, (int, float))
                ):
                    raise TypeError(
                        "max_distance doit être un nombre ou None."
                    )

                if max_distance < 0:
                    raise ValueError(
                        "max_distance ne peut pas être négative."
                    )

            # results = self._collection.query(
            #     query_embeddings=[embedding],
            #     n_results=top_k,
            # )
            query_kwargs = {
                "query_embeddings": [embedding],
                "n_results": top_k,
            }

            if document_id is not None:
                query_kwargs["where"] = {
                    "document_id": document_id
                }

            results = self._collection.query(
                **query_kwargs
            )

            ids = results["ids"][0]

            if not ids:
                return []

            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]

            search_results = build_search_results(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                distances=distances,
            )

            if max_distance is not None:
                search_results = [
                    result
                    for result in search_results
                    if result.distance <= max_distance
                ]

            return search_results
