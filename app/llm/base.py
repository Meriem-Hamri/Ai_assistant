from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """
    Interface de base pour les modèles de langage utilisés
    par l'application.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Génère une réponse à partir d'un prompt.

        Args:
            prompt: Prompt envoyé au modèle de langage.

        Returns:
            Réponse générée par le modèle.
        """
        pass