from app.embeddings.embedding_service import EmbeddingService
from app.llm.base import BaseLLM
from app.prompting.prompt_builder import PromptBuilder
from app.vectorstore.base import BaseVectorStore
from app.vectorstore.search_result import SearchResult

from app.rag.config import RAGConfig
from app.rag.exceptions import (
    RAGEmbeddingError,
    RAGGenerationError,
    RAGRetrievalError,
)
from app.rag.response import RAGResponse, Source


class RAGPipeline:
    """
    Orchestre l'ensemble du pipeline RAG.

    Le pipeline coordonne :

        Question
            ↓
        EmbeddingService
            ↓
        VectorStore
            ↓
        PromptBuilder
            ↓
        LLM
            ↓
        RAGResponse
    """

    NO_RESULTS_MESSAGE = (
        "Information non disponible dans les documents."
    )

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: BaseVectorStore,
        prompt_builder: PromptBuilder,
        llm: BaseLLM,
        config: RAGConfig,
    ) -> None:
        """
        Initialise le pipeline RAG.

        Les dépendances sont injectées depuis l'extérieur afin
        de conserver un faible couplage et de faciliter les tests.
        """

        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._prompt_builder = prompt_builder
        self._llm = llm
        self._config = config

    def answer(self, question: str) -> RAGResponse:
        """
        Génère une réponse à partir des documents indexés.

        Args:
            question:
                Question de l'utilisateur.

        Returns:
            Réponse RAG contenant la réponse et ses sources.

        Raises:
            ValueError:
                Si la question est vide.

            RAGEmbeddingError:
                Si la génération de l'embedding échoue.

            RAGRetrievalError:
                Si la recherche vectorielle échoue.

            RAGGenerationError:
                Si la génération du LLM échoue.
        """

        question = self._validate_question(question)

        query_embedding = self._generate_embedding(question)

        results = self._retrieve(query_embedding)

        if not results:
            return RAGResponse(
                answer=self.NO_RESULTS_MESSAGE,
                sources=[],
            )

        prompt = self._build_prompt(
            question=question,
            results=results,
        )

        answer = self._generate_answer(prompt)

        sources = self._build_sources(results)

        return RAGResponse(
            answer=answer,
            sources=sources,
        )

    @staticmethod
    def _validate_question(question: str) -> str:
        """
        Valide et normalise la question.
        """

        if not isinstance(question, str):
            raise TypeError(
                "La question doit être une chaîne de caractères."
            )

        question = question.strip()

        if not question:
            raise ValueError(
                "La question ne peut pas être vide."
            )

        return question

    def _generate_embedding(
        self,
        question: str,
    ) -> list[float]:
        """
        Génère l'embedding de la question.
        """

        try:
            return self._embedding_service.embed(question)

        except Exception as exc:
            raise RAGEmbeddingError(
                "Impossible de générer l'embedding de la question."
            ) from exc

    def _retrieve(
        self,
        query_embedding: list[float],
    ) -> list[SearchResult]:
        """
        Recherche les chunks les plus pertinents.
        """

        try:
            return self._vector_store.search(
                embedding=query_embedding,
                top_k=self._config.top_k,
            )

        except Exception as exc:
            raise RAGRetrievalError(
                "Impossible d'effectuer la recherche vectorielle."
            ) from exc

    def _build_prompt(
        self,
        question: str,
        results: list[SearchResult],
    ) -> str:
        """
        Construit le prompt destiné au LLM.
        """

        return self._prompt_builder.build(
            question=question,
            results=results,
        )

    def _generate_answer(
        self,
        prompt: str,
    ) -> str:
        """
        Génère la réponse avec le LLM.
        """

        try:
            return self._llm.generate(prompt)

        except Exception as exc:
            raise RAGGenerationError(
                "Impossible de générer la réponse avec le LLM."
            ) from exc

    @staticmethod
    def _build_sources(
        results: list[SearchResult],
    ) -> list[Source]:
        """
        Transforme les résultats de recherche en sources
        destinées à la réponse finale.
        """

        return [
            Source(
                document_id=result.document_id,
                document_name=result.document_name,
                page_number=result.page_number,
                chunk_id=result.chunk_id,
                distance=result.distance,
            )
            for result in results
        ]