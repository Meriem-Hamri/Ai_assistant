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

    retrieval_top_k: int = 20
    max_distance: float | None = None

    def __post_init__(self) -> None:

        if not isinstance(
            self.retrieval_top_k,
            int
        ):
            raise TypeError(
                "retrieval_top_k must be an integer"
            )

        if self.retrieval_top_k < 1:
            raise ValueError(
                "retrieval_top_k must be greater than or equal to 1"
            )

        if self.max_distance is not None:

            if not isinstance(
                self.max_distance,
                (int, float)
            ):
                raise TypeError(
                    "max_distance must be a number or None"
                )

            if self.max_distance < 0:
                raise ValueError(
                    "max_distance must be greater than or equal to 0"
                )