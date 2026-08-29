import pytest

from app.rag.config import RAGConfig
from app.rag.exceptions import (
    RAGEmbeddingError,
    RAGGenerationError,
    RAGRetrievalError,
)
from app.rag.pipeline import RAGPipeline
from app.vectorstore.search_result import SearchResult


class FakeEmbeddingService:
    """Faux service d'embedding utilisé pour les tests."""

    def __init__(self, embedding=None):
        self.embedding = embedding or [0.1, 0.2, 0.3]
        self.received_questions = []

    def embed(self, text: str):
        self.received_questions.append(text)
        return self.embedding


class FakeVectorStore:
    """Faux Vector Store utilisé pour les tests."""

    def __init__(self, results=None):
        self.results = results or []
        self.received_embeddings = []
        self.received_top_k = []
        self.received_max_distances = []

    def search(
        self,
        embedding,
        top_k=5,
        max_distance=None,
        document_id=None,
    ):
        self.received_embeddings.append(embedding)
        self.received_top_k.append(top_k)
        self.received_max_distances.append(max_distance)
        return self.results


class FakePromptBuilder:
    """Faux Prompt Builder utilisé pour les tests."""

    def __init__(self, prompt="PROMPT"):
        self.prompt = prompt
        self.received_questions = []
        self.received_results = []

    def build(self, question, results):
        self.received_questions.append(question)
        self.received_results.append(results)
        return self.prompt


class FakeLLM:
    """Faux LLM utilisé pour les tests."""

    def __init__(self, answer="Réponse générée."):
        self.answer = answer
        self.received_prompts = []

    def generate(self, prompt: str):
        self.received_prompts.append(prompt)
        return self.answer


def create_result(
    text: str = "Le contrat dure trois mois.",
    document_name: str = "contrat.pdf",
    document_id: str = "doc-1",
    page_number: int = 1,
) -> SearchResult:
    """
    Crée un SearchResult pour les tests.
    """

    return SearchResult(
        chunk_id="chunk-1",
        text=text,
        distance=0.05,
        document_id=document_id,
        document_name=document_name,
        page_number=page_number,
        chunk_index=0,
        start_char=0,
        end_char=len(text),
    )


def create_pipeline(
    results=None,
    llm_answer="Réponse générée.",
    top_k=5,
):
    """
    Crée un pipeline avec des dépendances simulées.
    """

    embedding_service = FakeEmbeddingService()

    vector_store = FakeVectorStore(
        results=results or []
    )

    prompt_builder = FakePromptBuilder()

    llm = FakeLLM(
        answer=llm_answer
    )

    config = RAGConfig(
        top_k=top_k
    )

    pipeline = RAGPipeline(
        embedding_service=embedding_service,
        vector_store=vector_store,
        prompt_builder=prompt_builder,
        llm=llm,
        config=config,
    )

    return (
        pipeline,
        embedding_service,
        vector_store,
        prompt_builder,
        llm,
    )


def test_question_is_trimmed():
    pipeline, embedding_service, _, _, _ = create_pipeline(
        results=[create_result()]
    )

    pipeline.answer("   Quelle est la durée du contrat ?   ")

    assert embedding_service.received_questions == [
        "Quelle est la durée du contrat ?"
    ]


def test_empty_question_is_rejected():
    pipeline, _, _, _, _ = create_pipeline()

    with pytest.raises(ValueError):
        pipeline.answer("")


def test_whitespace_question_is_rejected():
    pipeline, _, _, _, _ = create_pipeline()

    with pytest.raises(ValueError):
        pipeline.answer("   ")


def test_question_must_be_string():
    pipeline, _, _, _, _ = create_pipeline()

    with pytest.raises(TypeError):
        pipeline.answer(None)


def test_embedding_is_generated():
    pipeline, embedding_service, _, _, _ = create_pipeline(
        results=[create_result()]
    )

    question = "Quelle est la durée du contrat ?"

    pipeline.answer(question)

    assert embedding_service.received_questions == [question]


def test_vector_store_receives_embedding_and_top_k():
    results = [create_result()]

    (
        pipeline,
        embedding_service,
        vector_store,
        _,
        _,
    ) = create_pipeline(
        results=results,
        top_k=3,
    )

    pipeline.answer("Quelle est la durée du contrat ?")

    assert vector_store.received_embeddings == [
        embedding_service.embedding
    ]

    assert vector_store.received_top_k == [20]


def test_retrieval_query_is_enriched_for_technology_question():
    pipeline, embedding_service, _, _, _ = create_pipeline(
        results=[create_result()]
    )

    pipeline.answer("Quels frameworks ont été utilisés ?")

    assert embedding_service.received_questions == [
        "Quels frameworks ont été utilisés ?\n"
        "Chercher les outils logiciels, frameworks, technologies, "
        "bases de données et IDE utilisés."
    ]


def test_only_top_k_results_are_sent_to_prompt_builder():
    results = [
        create_result(text=f"Résultat {index}")
        for index in range(4)
    ]

    pipeline, _, _, prompt_builder, _ = create_pipeline(
        results=results,
        top_k=2,
    )

    pipeline.answer("Question")

    assert prompt_builder.received_results == [results[:2]]


def test_short_results_are_skipped_when_informative_results_exist():
    short_result = create_result(text="Titre")
    detailed_results = [
        create_result(
            text=f"Information détaillée {index}. " + "A" * 120,
        )
        for index in range(2)
    ]

    pipeline, _, _, prompt_builder, _ = create_pipeline(
        results=[short_result, *detailed_results],
        top_k=2,
    )

    pipeline.answer("Question")

    assert prompt_builder.received_results == [detailed_results]


def test_results_are_diversified_without_document_filter():
    results = [
        create_result(
            text=f"Information détaillée A {index}. " + "A" * 120,
            document_id="doc-a",
            document_name="a.pdf",
        )
        for index in range(4)
    ] + [
        create_result(
            text="Information détaillée B. " + "B" * 120,
            document_id="doc-b",
            document_name="b.pdf",
        )
    ]

    pipeline, _, _, prompt_builder, _ = create_pipeline(
        results=results,
        top_k=4,
    )

    pipeline.answer("Question")

    selected_results = prompt_builder.received_results[0]
    assert [result.document_id for result in selected_results] == [
        "doc-a",
        "doc-a",
        "doc-a",
        "doc-b",
    ]


def test_results_are_sent_to_prompt_builder():
    results = [
        create_result(),
        create_result(
            text="Le paiement est effectué chaque mois.",
            document_name="facture.pdf",
            page_number=2,
        ),
    ]

    (
        pipeline,
        _,
        _,
        prompt_builder,
        _,
    ) = create_pipeline(
        results=results
    )

    pipeline.answer("Comment fonctionne le paiement ?")

    assert prompt_builder.received_questions == [
        "Comment fonctionne le paiement ?"
    ]

    assert prompt_builder.received_results == [results]


def test_prompt_is_sent_to_llm():
    (
        pipeline,
        _,
        _,
        prompt_builder,
        llm,
    ) = create_pipeline(
        results=[create_result()]
    )

    pipeline.answer("Quelle est la durée du contrat ?")

    assert llm.received_prompts == [
        prompt_builder.prompt
    ]


def test_answer_is_returned():
    expected_answer = "Le contrat dure trois mois."

    (
        pipeline,
        _,
        _,
        _,
        _,
    ) = create_pipeline(
        results=[create_result()],
        llm_answer=expected_answer,
    )

    response = pipeline.answer(
        "Quelle est la durée du contrat ?"
    )

    assert response.answer == expected_answer


def test_sources_are_created_from_search_results():
    result = create_result(
        document_name="contrat.pdf",
        page_number=4,
    )

    (
        pipeline,
        _,
        _,
        _,
        _,
    ) = create_pipeline(
        results=[result]
    )

    response = pipeline.answer(
        "Quelle est la durée du contrat ?"
    )

    assert len(response.sources) == 1

    source = response.sources[0]

    assert source.document_id == "doc-1"
    assert source.document_name == "contrat.pdf"
    assert source.page_number == 4
    assert source.chunk_id == "chunk-1"
    assert source.distance == 0.05


def test_no_results_returns_message_without_calling_llm():
    (
        pipeline,
        _,
        _,
        _,
        llm,
    ) = create_pipeline(
        results=[]
    )

    response = pipeline.answer(
        "Question sans résultat"
    )

    assert response.answer == (
        "Information non disponible dans les documents."
    )

    assert response.sources == []

    assert llm.received_prompts == []


def test_embedding_error_is_translated_to_rag_error():
    class FailingEmbeddingService:
        def embed(self, text):
            raise RuntimeError("Embedding failure")

    vector_store = FakeVectorStore()
    prompt_builder = FakePromptBuilder()
    llm = FakeLLM()

    pipeline = RAGPipeline(
        embedding_service=FailingEmbeddingService(),
        vector_store=vector_store,
        prompt_builder=prompt_builder,
        llm=llm,
        config=RAGConfig(),
    )

    with pytest.raises(RAGEmbeddingError):
        pipeline.answer("Question")


def test_retrieval_error_is_translated_to_rag_error():
    class FailingVectorStore:
        def search(
            self,
            embedding,
            top_k,
            max_distance=None,
            document_id=None,
        ):
            raise RuntimeError("Retrieval failure")

    pipeline = RAGPipeline(
        embedding_service=FakeEmbeddingService(),
        vector_store=FailingVectorStore(),
        prompt_builder=FakePromptBuilder(),
        llm=FakeLLM(),
        config=RAGConfig(),
    )

    with pytest.raises(RAGRetrievalError):
        pipeline.answer("Question")


def test_generation_error_is_translated_to_rag_error():
    class FailingLLM:
        def generate(self, prompt):
            raise RuntimeError("Generation failure")

    pipeline = RAGPipeline(
        embedding_service=FakeEmbeddingService(),
        vector_store=FakeVectorStore(
            results=[create_result()]
        ),
        prompt_builder=FakePromptBuilder(),
        llm=FailingLLM(),
        config=RAGConfig(),
    )

    with pytest.raises(RAGGenerationError):
        pipeline.answer("Question")
