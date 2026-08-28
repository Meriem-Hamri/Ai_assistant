from app.chunking.natural_chunker import NaturalChunker


class DocumentIndexer:
    """
    Responsable de la préparation et de l'indexation
    d'un document dans le vector store.
    """

    def __init__(
        self,
        embedding_service,
        vector_store,
    ) -> None:
        self._chunker = NaturalChunker()
        self._embedding_service = embedding_service
        self._vector_store = vector_store

    def index(self, document):
        """
        Découpe, vectorise et indexe un document.

        Returns:
            Les chunks créés et indexés.
        """

        chunks = self._chunker.chunk(document)

        if not chunks:
            raise ValueError(
                "Aucun contenu exploitable dans le document."
            )

        embeddings = self._embedding_service.embed_batch(
            [chunk.text for chunk in chunks]
        )

        self._vector_store.add_chunks(
            chunks=chunks,
            embeddings=embeddings,
        )

        return chunks