from dataclasses import dataclass


@dataclass(frozen=True)
class RAGConfig:
    """
    Configuration du pipeline RAG.

    Attributes:
        top_k: Nombre maximum de résultats à récupérer
            depuis le Vector Store.
    """

    top_k: int = 5

    def __post_init__(self) -> None:
        """Valide la configuration après son initialisation."""

        if not isinstance(self.top_k, int):
            raise TypeError("top_k must be an integer")

        if self.top_k < 1:
            raise ValueError("top_k must be greater than or equal to 1")