from abc import ABC, abstractmethod

import numpy as np


class BaseEmbeddingModel(ABC):
    """
    Interface commune à tous les modèles d'embedding.

    Chaque implémentation doit être capable de :
    - générer un embedding pour un texte ;
    - générer des embeddings pour plusieurs textes.
    """

    @abstractmethod
    def embed(self, text: str) -> np.ndarray:
        """
        Génère l'embedding d'un texte.

        Args:
            text: Texte à encoder.

        Returns:
            Un vecteur numpy représentant le texte.
        """
        raise NotImplementedError

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Génère les embeddings de plusieurs textes.

        Args:
            texts: Liste de textes.

        Returns:
            Une matrice numpy contenant un embedding par texte.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Retourne la dimension des embeddings produits.
        """
        raise NotImplementedError