from sentence_transformers import SentenceTransformer
import numpy as np
import torch

from app.embeddings.base import BaseEmbeddingModel


class BGEM3Embedding(BaseEmbeddingModel):
    """
    Implémentation du modèle BGE-M3.

    Cette classe encapsule entièrement SentenceTransformer afin que
    le reste du projet ne dépende jamais directement de cette bibliothèque.
    """

    MODEL_NAME = "BAAI/bge-m3"

    def __init__(self, device: str | None = None):
        """
        Initialise le modèle.

        Args:
            device:
                "cpu", "cuda" ou None.
                Si None, le périphérique est choisi automatiquement.
        """

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self._device = device

        self._model = SentenceTransformer(
            self.MODEL_NAME,
            device=device
        )

    @property
    def dimension(self) -> int:
        """
        Retourne la dimension des embeddings produits.
        """
        return self._model.get_sentence_embedding_dimension()

    @property
    def device(self) -> str:
        """
        Retourne le périphérique utilisé.
        """
        return self._device

    def embed(self, text: str) -> np.ndarray:
        """
        Génère l'embedding d'un texte.
        """

        return self._model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Génère les embeddings d'une liste de textes.
        """

        return self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
    def __repr__(self):
     return (
        f"BGEM3Embedding("
        f"device={self.device}, "
        f"dimension={self.dimension})"
     )