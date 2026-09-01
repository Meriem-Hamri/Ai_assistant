import json
import logging
import re
import time

from app.embeddings.embedding_service import EmbeddingService
from app.llm.base import BaseLLM
from app.prompting.prompt_builder import PromptBuilder
from app.vectorstore.base import BaseVectorStore
from app.vectorstore.filters import DocumentFilters, normalize_document_ids
from app.vectorstore.search_result import SearchResult

from app.rag.config import RAGConfig
from app.rag.exceptions import (
    RAGEmbeddingError,
    RAGGenerationError,
    RAGRetrievalError,
)
from app.rag.response import RAGResponse, Source


logger = logging.getLogger(__name__)

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

    _TECHNOLOGY_QUERY_TERMS = (
        "framework",
        "technolog",
        "outil",
        "logiciel",
        "ide",
        "base de donn",
        "architecture",
    )

    _TECHNOLOGY_QUERY_CONTEXT = (
        "Chercher les outils logiciels, frameworks, technologies, "
        "bases de données et IDE utilisés."
    )

    _COMPARATIVE_QUESTION_MARKERS = (
        "point commun",
        "lien commun",
        "lien en commun",
        "différence",
        "différences",
        "difference",
        "differences",
        "compare",
        "comparer",
        "comparaison",
        "entre ces documents",
        "ces deux documents",
        "ces documents",
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

    def answer(
        self,
        question: str,
        document_ids: list[str] | tuple[str, ...] = (),
        filters: DocumentFilters | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> RAGResponse:
        """
        Génère une réponse à partir des documents indexés.

        Args:
            question:
                Question de l'utilisateur.

            document_ids:
                Documents à interroger. None ou une collection vide
                recherche dans tous les documents.

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
        normalized_document_ids = normalize_document_ids(document_ids)
        conversation_history = list(conversation_history or [])
        is_comparative_question = self._is_comparative_question(
            question,
            normalized_document_ids,
        )

        start = time.perf_counter()

        # Embedding
        t0 = time.perf_counter()

        if is_comparative_question:
            retrieval_query = question
        else:
            retrieval_query = self._build_retrieval_query(
                question,
                conversation_history,
            )
        query_embedding = self._generate_embedding(retrieval_query)

        print(f"[TIME] Embedding : {time.perf_counter() - t0:.2f}s")

        t0 = time.perf_counter()
        results = self._retrieve(
            query_embedding,
            normalized_document_ids,
            filters,
        )

        if is_comparative_question:
            results = self._ensure_comparative_document_coverage(
                query_embedding=query_embedding,
                results=results,
                document_ids=normalized_document_ids,
                filters=filters,
            )

        print(f"[TIME] Retrieval : {time.perf_counter() - t0:.2f}s")
        if (
            not results
            or (
                is_comparative_question
                and self._find_missing_document_ids(
                    results,
                    normalized_document_ids,
                )
            )
        ):
            return RAGResponse(
                answer=self.NO_RESULTS_MESSAGE,
                sources=[],
            )

        selected_results = self._select_results(
            results,
            document_ids=normalized_document_ids,
            is_comparative_question=is_comparative_question,
        )

        # Prompt
        t0 = time.perf_counter()
        prompt = self._build_prompt(
            question=question,
            results=selected_results,
            conversation_history=conversation_history,
        )
        print(f"[TIME] Prompt : {time.perf_counter() - t0:.2f}s")

        # LLM
        t0 = time.perf_counter()
        generated_content = self._generate_answer(prompt)
        print(f"[TIME] LLM : {time.perf_counter() - t0:.2f}s")
        answer, used_source_ids = self._parse_generation(generated_content)

        if self._is_no_results_answer(answer):
            sources = []
        elif used_source_ids is None:
            logger.warning(
                "Impossible de parser les citations du LLM; "
                "aucune source ne sera exposee."
            )
            sources = []
        else:
            sources = self._build_used_sources(
                results=selected_results,
                used_source_ids=used_source_ids,
            )

        print(
            f"[TIME] TOTAL : "
            f"{time.perf_counter() - start:.2f}s"
        )

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
        document_ids: tuple[str, ...] = (),
        filters: DocumentFilters | None = None,
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """
        Recherche les chunks les plus pertinents.
        """

        try:
            results = self._vector_store.search(
                embedding=query_embedding,
                top_k=(
                    self._config.retrieval_top_k
                    if top_k is None
                    else top_k
                ),
                max_distance=self._config.max_distance,
                document_ids=document_ids,
                filters=filters,
            )

            print("\n========== RETRIEVAL ==========")

            for result in results:
                print(
                    f"page={result.page_number} | "
                    f"distance={result.distance:.4f} | "
                    f"chars={len(result.text)} | "
                    f"document={result.document_name}"
                )
                #print(result.text[:500])
                print("-" * 60)

            return results

        except Exception as exc:
            raise RAGRetrievalError(
                "Impossible d'effectuer la recherche vectorielle."
            ) from exc

    def _ensure_comparative_document_coverage(
        self,
        query_embedding: list[float],
        results: list[SearchResult],
        document_ids: tuple[str, ...],
        filters: DocumentFilters | None,
    ) -> list[SearchResult]:
        """Complète une comparaison avec des passages de chaque document."""

        merged_results = list(results)

        for document_id in self._find_missing_document_ids(
            merged_results,
            document_ids,
        ):
            merged_results.extend(
                self._retrieve(
                    query_embedding=query_embedding,
                    document_ids=(document_id,),
                    filters=filters,
                    top_k=self._config.max_results_per_document,
                )
            )

        unique_results: list[SearchResult] = []
        seen_chunk_ids: set[str] = set()

        for result in merged_results:
            if result.chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(result.chunk_id)
            unique_results.append(result)

        return unique_results

    @staticmethod
    def _find_missing_document_ids(
        results: list[SearchResult],
        document_ids: tuple[str, ...],
    ) -> tuple[str, ...]:
        present_document_ids = {
            result.document_id
            for result in results
        }
        return tuple(
            document_id
            for document_id in document_ids
            if document_id not in present_document_ids
        )

    @classmethod
    def _build_retrieval_query(
        cls,
        question: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        """Enrichit la recherche avec les derniers messages utilisateur."""

        recent_user_messages = [
            message["content"].strip()
            for message in conversation_history or []
            if (
                message.get("role") == "user"
                and isinstance(message.get("content"), str)
                and message["content"].strip()
            )
        ][-2:]

        if recent_user_messages:
            recent_history = "\n\n".join(recent_user_messages)
            retrieval_query = (
                "Contexte utilisateur récent:\n"
                f"{recent_history}\n\n"
                "Question actuelle:\n"
                f"{question}"
            )
        else:
            retrieval_query = question

        normalized_question = question.casefold()

        if any(
            term in normalized_question
            for term in cls._TECHNOLOGY_QUERY_TERMS
        ):
            return (
                f"{retrieval_query}\n"
                f"{cls._TECHNOLOGY_QUERY_CONTEXT}"
            )

        return retrieval_query

    @classmethod
    def _is_comparative_question(
        cls,
        question: str,
        document_ids: tuple[str, ...],
    ) -> bool:
        """Détecte les comparaisons explicites portant sur plusieurs documents."""

        if len(document_ids) < 2:
            return False

        normalized_question = question.casefold()
        return any(
            marker in normalized_question
            for marker in cls._COMPARATIVE_QUESTION_MARKERS
        )

    def _select_results(
        self,
        results: list[SearchResult],
        document_ids: tuple[str, ...],
        is_comparative_question: bool = False,
    ) -> list[SearchResult]:
        """Conserve les passages les mieux classés pour le prompt RAG."""

        informative_results = [
            result
            for result in results
            if len(result.text.strip()) >= self._config.min_result_characters
        ]

        candidate_results = informative_results or results

        if is_comparative_question:
            selected_results = self._select_comparative_results(
                results=results,
                candidate_results=candidate_results,
                document_ids=document_ids,
            )
        elif len(document_ids) == 1:
            selected_results = candidate_results[:self._config.top_k]
        else:
            selected_results = self._select_diverse_documents(
                candidate_results,
            )

        candidate_document_ids = {
            result.document_id
            for result in candidate_results
        }

        if (
            len(selected_results) < self._config.top_k
            and (
                len(document_ids) == 1
                or len(candidate_document_ids) == 1
            )
        ):
            selected_chunk_ids = {
                result.chunk_id
                for result in selected_results
            }
            selected_results.extend(
                result
                for result in candidate_results
                if result.chunk_id not in selected_chunk_ids
            )
            selected_results = selected_results[:self._config.top_k]

        print(
            "[RETRIEVAL] Passages envoyés au prompt : "
            f"{len(selected_results)}/{len(results)} "
            f"(candidats informatifs : {len(informative_results)})"
        )

        return selected_results

    def _select_comparative_results(
        self,
        results: list[SearchResult],
        candidate_results: list[SearchResult],
        document_ids: tuple[str, ...],
    ) -> list[SearchResult]:
        """Réserve le meilleur passage disponible de chaque document."""

        selected_results: list[SearchResult] = []
        selected_chunk_ids: set[str] = set()
        result_count_by_document: dict[str, int] = {}

        for document_id in document_ids:
            representative = next(
                (
                    result
                    for result in candidate_results
                    if result.document_id == document_id
                ),
                None,
            )
            if representative is None:
                representative = next(
                    (
                        result
                        for result in results
                        if result.document_id == document_id
                    ),
                    None,
                )
            if representative is None:
                continue

            selected_results.append(representative)
            selected_chunk_ids.add(representative.chunk_id)
            result_count_by_document[document_id] = 1

            if len(selected_results) == self._config.top_k:
                return selected_results

        for result in candidate_results:
            if result.chunk_id in selected_chunk_ids:
                continue

            document_result_count = result_count_by_document.get(
                result.document_id,
                0,
            )
            if document_result_count >= self._config.max_results_per_document:
                continue

            selected_results.append(result)
            selected_chunk_ids.add(result.chunk_id)
            result_count_by_document[result.document_id] = (
                document_result_count + 1
            )

            if len(selected_results) == self._config.top_k:
                break

        return selected_results

    def _select_diverse_documents(
        self,
        results: list[SearchResult],
    ) -> list[SearchResult]:
        """Conserve le classement tout en limitant un document dominant."""

        selected_results: list[SearchResult] = []
        result_count_by_document: dict[str, int] = {}

        for result in results:
            document_result_count = result_count_by_document.get(
                result.document_id,
                0,
            )

            if document_result_count >= self._config.max_results_per_document:
                continue

            selected_results.append(result)
            result_count_by_document[result.document_id] = (
                document_result_count + 1
            )

            if len(selected_results) == self._config.top_k:
                break

        return selected_results

    def _build_prompt(
        self,
        question: str,
        results: list[SearchResult],
        conversation_history: list[dict[str, str]],
    ) -> str:
        """
        Construit le prompt destiné au LLM.
        """

        return self._prompt_builder.build(
            question=question,
            results=results,
            conversation_history=conversation_history,
        )

    def _generate_answer(
        self,
        prompt: str,
    ) -> str:
        """
        Génère la réponse avec le LLM.
        """
        print("\n" + "=" * 70)
        print("PROMPT ENVOYÉ AU LLM")
        print("=" * 70)
        # print(prompt)  # Diagnostic ponctuel : ne pas journaliser le document complet.
        print("=" * 70)

        try:
            return self._llm.generate(prompt)

        except Exception as exc:
            raise RAGGenerationError(
                "Impossible de générer la réponse avec le LLM."
            ) from exc

    @staticmethod
    def _parse_generation(
        generated_content: str,
    ) -> tuple[str, list[str] | None]:
        """Extract the public answer and citation IDs from the LLM JSON."""

        decoder = json.JSONDecoder()

        for match in re.finditer(r"\{", generated_content):
            try:
                payload, _ = decoder.raw_decode(
                    generated_content[match.start():]
                )
            except json.JSONDecodeError:
                continue

            if not isinstance(payload, dict):
                continue

            answer = payload.get("answer")
            used_sources = payload.get("used_sources")

            if not isinstance(answer, str) or not isinstance(
                used_sources, list
            ):
                continue

            if not all(isinstance(source_id, str) for source_id in used_sources):
                continue

            return answer.strip(), used_sources

        answer = RAGPipeline._recover_truncated_answer(generated_content)
        if answer is None:
            plain_answer = generated_content.strip()
            contains_internal_protocol = re.search(
                r'"(?:answer|used_sources)"\s*:',
                generated_content,
            )
            if plain_answer and contains_internal_protocol is None:
                return plain_answer, None

            return RAGPipeline.NO_RESULTS_MESSAGE, []

        used_sources = RAGPipeline._recover_truncated_used_sources(
            generated_content
        )
        return answer, used_sources

    @staticmethod
    def _recover_truncated_answer(generated_content: str) -> str | None:
        """Recover only the JSON ``answer`` value from incomplete output."""

        field_match = re.search(r'"answer"\s*:\s*"', generated_content)
        if field_match is None:
            return None

        value_start = field_match.end()
        recovered: list[str] = []
        index = value_start
        escape_values = {
            '"': '"',
            "\\": "\\",
            "/": "/",
            "b": "\b",
            "f": "\f",
            "n": "\n",
            "r": "\r",
            "t": "\t",
        }

        while index < len(generated_content):
            character = generated_content[index]

            if character == '"':
                if re.match(
                    r'"used_sources"\s*:',
                    generated_content[index:],
                ):
                    while recovered and recovered[-1].isspace():
                        recovered.pop()
                    if recovered and recovered[-1] == ",":
                        recovered.pop()
                break

            if character != "\\":
                recovered.append(character)
                index += 1
                continue

            if index + 1 >= len(generated_content):
                break

            escaped_character = generated_content[index + 1]
            if escaped_character in escape_values:
                recovered.append(escape_values[escaped_character])
                index += 2
                continue

            if escaped_character == "u":
                unicode_escape = generated_content[index:index + 6]
                if re.fullmatch(r"\\u[0-9a-fA-F]{4}", unicode_escape):
                    codepoint = int(unicode_escape[2:], 16)
                    next_escape = generated_content[index + 6:index + 12]
                    if (
                        0xD800 <= codepoint <= 0xDBFF
                        and re.fullmatch(
                            r"\\u[0-9a-fA-F]{4}",
                            next_escape,
                        )
                    ):
                        low_surrogate = int(next_escape[2:], 16)
                        if 0xDC00 <= low_surrogate <= 0xDFFF:
                            recovered.append(chr(
                                0x10000
                                + ((codepoint - 0xD800) << 10)
                                + (low_surrogate - 0xDC00)
                            ))
                            index += 12
                            continue
                    if 0xD800 <= codepoint <= 0xDFFF:
                        recovered.append(unicode_escape)
                    else:
                        recovered.append(chr(codepoint))
                    index += 6
                    continue

            # Preserve an unknown escape as user text instead of applying a
            # global replacement to the model protocol.
            recovered.extend(("\\", escaped_character))
            index += 2

        answer = "".join(recovered).strip()
        return answer or None

    @staticmethod
    def _recover_truncated_used_sources(
        generated_content: str,
    ) -> list[str] | None:
        """Recover valid SOURCE_N IDs from an incomplete citations array."""

        field_match = re.search(
            r'"used_sources"\s*:\s*\[',
            generated_content,
        )
        if field_match is None:
            return None

        array_content = generated_content[field_match.end():]
        array_end = array_content.find("]")
        if array_end >= 0:
            array_content = array_content[:array_end]

        source_ids: list[str] = []
        seen_source_ids: set[str] = set()
        index = 0

        while index < len(array_content):
            quote_start = array_content.find('"', index)
            if quote_start < 0:
                break

            quote_end = quote_start + 1
            while quote_end < len(array_content):
                if array_content[quote_end] == '"':
                    preceding_backslashes = 0
                    backslash_index = quote_end - 1
                    while (
                        backslash_index > quote_start
                        and array_content[backslash_index] == "\\"
                    ):
                        preceding_backslashes += 1
                        backslash_index -= 1
                    if preceding_backslashes % 2 == 0:
                        break
                quote_end += 1

            source_id = array_content[quote_start + 1:quote_end]
            source_id = source_id.strip().upper()
            index = quote_end + 1

            if re.fullmatch(r"SOURCE_[0-9]+", source_id) is None:
                continue
            if source_id in seen_source_ids:
                continue

            seen_source_ids.add(source_id)
            source_ids.append(source_id)

        return source_ids or None

    @classmethod
    def _is_no_results_answer(cls, answer: str) -> bool:
        """Recognize the configured fallback despite minor punctuation changes."""

        def normalize(value: str) -> str:
            return " ".join(
                value.casefold().strip().rstrip(".!? ").split()
            )

        return normalize(answer) == normalize(cls.NO_RESULTS_MESSAGE)

    @classmethod
    def _build_used_sources(
        cls,
        results: list[SearchResult],
        used_source_ids: list[str],
    ) -> list[Source]:
        """Map valid citation IDs to real passages, preserving cited order."""

        result_by_source_id = {
            f"SOURCE_{index}": result
            for index, result in enumerate(results, start=1)
        }
        seen_source_ids: set[str] = set()
        used_results: list[SearchResult] = []

        for source_id in used_source_ids:
            normalized_source_id = source_id.strip().upper()
            result = result_by_source_id.get(normalized_source_id)

            if result is None or normalized_source_id in seen_source_ids:
                continue

            seen_source_ids.add(normalized_source_id)
            used_results.append(result)

        return cls._build_sources(used_results)

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
                excerpt=result.text.strip(),
                distance=result.distance,
            )
            for result in results
        ]
