from app.embeddings.base import BaseEmbeddingModel
from app.embeddings.models.bge_m3 import BGEM3Embedding


class EmbeddingService:
    """
    Service responsable de la génération des embeddings.

    Cette classe constitue le point d'entrée unique du module
    Embeddings pour le reste de l'application.
    """

    def __init__(self, model: BaseEmbeddingModel | None = None):
        """
        Initialise le service.

        Si aucun modèle n'est fourni, BGE-M3 est utilisé.
        """

        self._model = model or BGEM3Embedding()

    @property
    def model(self) -> BaseEmbeddingModel:
        """
        Retourne le modèle utilisé.
        """
        return self._model

    def embed(self, text: str):
        """
        Génère l'embedding d'un texte.
        """
        return self._model.embed(text)

    def embed_batch(self, texts: list[str]):
        """
        Génère les embeddings d'une liste de textes.
        """
        return self._model.embed_batch(texts)

    @property
    def dimension(self):
        """
        Retourne la dimension des embeddings.
        """
        return self._model.dimension