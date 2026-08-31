from dataclasses import dataclass


# @dataclass(frozen=True)
# class RAGConfig:
#     """
#     Configuration du pipeline RAG.

#     Attributes:
#         top_k: Nombre maximum de résultats à récupérer
#             depuis le Vector Store.
#     """

#     top_k: int = 5
#     max_distance: float | None = 0.5

#     def __post_init__(self) -> None:
#         """Valide la configuration après son initialisation."""

#         if not isinstance(self.top_k, int):
#             raise TypeError("top_k must be an integer")

#         if self.top_k < 1:
#             raise ValueError("top_k must be greater than or equal to 1")

@dataclass(frozen=True)
class RAGConfig:
    """
    Configuration du pipeline RAG.
    """

    # Nombre de résultats récupérés initialement depuis Chroma
    retrieval_top_k: int = 20

    # Nombre maximum de résultats réellement envoyés au LLM
    top_k: int = 10

    # Les fragments très courts sont généralement des entrées de sommaire ou
    # des titres isolés, insuffisants pour répondre à une question RAG.
    min_result_characters: int = 120

    # Sans filtre document, évite que les meilleurs chunks d'un seul fichier
    # masquent tous les autres documents pertinents.
    max_results_per_document: int = 3

    # Distance maximale autorisée.
    # None = aucun filtrage fixe.
    max_distance: float | None = None

    def __post_init__(self) -> None:

        if not isinstance(self.retrieval_top_k, int):
            raise TypeError(
                "retrieval_top_k doit être un entier."
            )

        if self.retrieval_top_k < 1:
            raise ValueError(
                "retrieval_top_k doit être supérieur ou égal à 1."
            )

        if not isinstance(self.top_k, int):
            raise TypeError(
                "top_k doit être un entier."
            )

        if self.top_k < 1:
            raise ValueError(
                "top_k doit être supérieur ou égal à 1."
            )

        if self.top_k > self.retrieval_top_k:
            raise ValueError(
                "top_k ne peut pas être supérieur "
                "à retrieval_top_k."
            )

        if not isinstance(self.min_result_characters, int):
            raise TypeError(
                "min_result_characters doit être un entier."
            )

        if self.min_result_characters < 0:
            raise ValueError(
                "min_result_characters ne peut pas être négatif."
            )

        if not isinstance(self.max_results_per_document, int):
            raise TypeError(
                "max_results_per_document doit être un entier."
            )

        if self.max_results_per_document < 1:
            raise ValueError(
                "max_results_per_document doit être supérieur ou égal à 1."
            )

        if self.max_distance is not None:

            if (
                isinstance(self.max_distance, bool)
                or not isinstance(
                    self.max_distance,
                    (int, float),
                )
            ):
                raise TypeError(
                    "max_distance doit être un nombre ou None."
                )

            if self.max_distance < 0:
                raise ValueError(
                    "max_distance ne peut pas être négative."
                )
