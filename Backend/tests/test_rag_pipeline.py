import pytest

from app.prompting.prompt_builder import PromptBuilder
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

    def __init__(self, results=None, results_by_document_ids=None):
        self.results = [] if results is None else results
        self.results_by_document_ids = results_by_document_ids or {}
        self.received_embeddings = []
        self.received_top_k = []
        self.received_max_distances = []
        self.received_filters = []
        self.received_document_ids = []

    def search(
        self,
        embedding,
        top_k=5,
        max_distance=None,
        document_ids=None,
        filters=None,
    ):
        self.received_embeddings.append(embedding)
        self.received_top_k.append(top_k)
        self.received_max_distances.append(max_distance)
        self.received_filters.append(filters)
        self.received_document_ids.append(document_ids)
        key = tuple(document_ids or ())
        results = self.results_by_document_ids.get(key, self.results)
        return results[:top_k]


class FakePromptBuilder:
    """Faux Prompt Builder utilisé pour les tests."""

    def __init__(self, prompt="PROMPT"):
        self.prompt = prompt
        self.received_questions = []
        self.received_results = []
        self.received_histories = []

    def build(self, question, results, conversation_history=None):
        self.received_questions.append(question)
        self.received_results.append(results)
        self.received_histories.append(conversation_history)
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
    chunk_id: str = "chunk-1",
) -> SearchResult:
    """
    Crée un SearchResult pour les tests.
    """

    return SearchResult(
        chunk_id=chunk_id,
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
    results_by_document_ids=None,
):
    """
    Crée un pipeline avec des dépendances simulées.
    """

    embedding_service = FakeEmbeddingService()

    vector_store = FakeVectorStore(
        results=results,
        results_by_document_ids=results_by_document_ids,
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


def test_vector_store_receives_document_filters():
    pipeline, _, vector_store, _, _ = create_pipeline(
        results=[create_result()]
    )

    from app.vectorstore.filters import DocumentFilters

    filters = DocumentFilters(
        category="finance",
        year=2016,
        tags=("salaire",),
    )
    pipeline.answer("Quelle est la rémunération ?", filters=filters)

    assert vector_store.received_filters == [filters]


@pytest.mark.parametrize(
    ("document_ids", "expected"),
    [
        (None, ()),
        ([], ()),
        (["A"], ("A",)),
        ([" A ", "B", "A", ""], ("A", "B")),
    ],
)
def test_vector_store_receives_normalized_document_ids(
    document_ids,
    expected,
):
    pipeline, _, vector_store, _, _ = create_pipeline(
        results=[create_result()]
    )

    pipeline.answer("Question", document_ids=document_ids)

    assert vector_store.received_document_ids == [expected]


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


def test_retrieval_query_uses_only_two_latest_user_messages():
    pipeline, embedding_service, _, prompt_builder, _ = create_pipeline(
        results=[create_result()]
    )
    history = [
        {"role": "user", "content": "Ancienne question"},
        {"role": "assistant", "content": "Réponse à ignorer pour le retrieval"},
        {"role": "user", "content": "Avant-dernière question"},
        {"role": "assistant", "content": "Autre réponse à ignorer"},
        {"role": "user", "content": "Dernière question"},
    ]

    pipeline.answer(
        "Question actuelle",
        conversation_history=history,
    )

    assert embedding_service.received_questions == [
        "Contexte utilisateur récent:\n"
        "Avant-dernière question\n\n"
        "Dernière question\n\n"
        "Question actuelle:\n"
        "Question actuelle"
    ]
    assert prompt_builder.received_histories == [history]
    assert prompt_builder.received_questions == ["Question actuelle"]


def test_none_history_is_normalized_before_prompt_builder():
    pipeline, embedding_service, _, prompt_builder, _ = create_pipeline(
        results=[create_result()]
    )

    pipeline.answer("Question autonome", conversation_history=None)

    assert embedding_service.received_questions == ["Question autonome"]
    assert prompt_builder.received_histories == [[]]


def test_results_are_not_diversified_for_one_selected_document():
    results = [
        create_result(
            text=f"Information détaillée {index}. " + "A" * 120,
            document_id="doc-a",
            chunk_id=f"chunk-{index}",
        )
        for index in range(4)
    ]
    pipeline, _, _, prompt_builder, _ = create_pipeline(
        results=results,
        top_k=4,
    )

    pipeline.answer("Question", document_ids=["doc-a"])

    assert prompt_builder.received_results == [results]


def test_results_are_diversified_for_multiple_selected_documents():
    results = [
        create_result(
            text=f"Information détaillée A {index}. " + "A" * 120,
            document_id="doc-a",
            chunk_id=f"chunk-a-{index}",
        )
        for index in range(4)
    ] + [
        create_result(
            text="Information détaillée B. " + "B" * 120,
            document_id="doc-b",
            chunk_id="chunk-b",
        )
    ]
    pipeline, _, _, prompt_builder, _ = create_pipeline(
        results=results,
        top_k=4,
    )

    pipeline.answer("Question", document_ids=["doc-a", "doc-b"])

    assert [
        result.document_id
        for result in prompt_builder.received_results[0]
    ] == ["doc-a", "doc-a", "doc-a", "doc-b"]


def test_normal_multi_document_question_keeps_existing_retrieval_behavior():
    result = create_result(
        text="Information détaillée A. " + "A" * 120,
        document_id="doc-a",
        chunk_id="chunk-a",
    )
    pipeline, _, vector_store, prompt_builder, llm = create_pipeline(
        results=[result]
    )

    pipeline.answer(
        "Quelle information est disponible ?",
        document_ids=["doc-a", "doc-b"],
    )

    assert vector_store.received_document_ids == [("doc-a", "doc-b")]
    assert prompt_builder.received_results == [[result]]
    assert llm.received_prompts == [prompt_builder.prompt]


def test_comparative_question_with_global_coverage_needs_no_targeted_search():
    results = [
        create_result(
            text="Information détaillée A. " + "A" * 120,
            document_id="doc-a",
            chunk_id="chunk-a",
        ),
        create_result(
            text="Information détaillée B. " + "B" * 120,
            document_id="doc-b",
            chunk_id="chunk-b",
        ),
    ]
    pipeline, _, vector_store, prompt_builder, _ = create_pipeline(
        results=results
    )

    pipeline.answer(
        "Quel est leur point commun ?",
        document_ids=["doc-a", "doc-b"],
    )

    assert vector_store.received_document_ids == [("doc-a", "doc-b")]
    assert {
        result.document_id
        for result in prompt_builder.received_results[0]
    } == {"doc-a", "doc-b"}


def test_comparative_question_targets_missing_document_with_same_embedding():
    result_a = create_result(
        text="Information détaillée A. " + "A" * 120,
        document_id="doc-a",
        chunk_id="chunk-a",
    )
    results_b = [
        create_result(
            text=f"Information détaillée B {index}. " + "B" * 120,
            document_id="doc-b",
            chunk_id=f"chunk-b-{index}",
        )
        for index in range(4)
    ]
    pipeline, embedding_service, vector_store, prompt_builder, _ = (
        create_pipeline(
            results_by_document_ids={
                ("doc-a", "doc-b"): [result_a],
                ("doc-b",): results_b,
            }
        )
    )

    pipeline.answer(
        "Existe-t-il un lien en commun entre ces documents ?",
        document_ids=["doc-a", "doc-b"],
    )

    assert vector_store.received_document_ids == [
        ("doc-a", "doc-b"),
        ("doc-b",),
    ]
    assert vector_store.received_top_k == [20, 3]
    assert vector_store.received_embeddings[0] is embedding_service.embedding
    assert vector_store.received_embeddings[1] is embedding_service.embedding
    selected_results = prompt_builder.received_results[0]
    assert sum(
        result.document_id == "doc-b"
        for result in selected_results
    ) == 3
    assert {result.document_id for result in selected_results} == {
        "doc-a",
        "doc-b",
    }


def test_grounded_comparison_from_two_documents_is_not_replaced_by_fallback():
    result_a = create_result(
        text=(
            "Le tableau de bord utilise des indicateurs pour suivre "
            "l'activite et faciliter l'analyse des donnees."
        ),
        document_name="final.pdf",
        document_id="doc-a",
        chunk_id="chunk-a",
    )
    result_b = create_result(
        text=(
            "Le rapport utilise des indicateurs pour suivre l'evolution "
            "de la consommation et des emissions."
        ),
        document_name="Environnement.docx",
        document_id="doc-b",
        chunk_id="chunk-b",
    )
    embedding_service = FakeEmbeddingService()
    vector_store = FakeVectorStore(
        results_by_document_ids={
            ("doc-a", "doc-b"): [result_a],
            ("doc-b",): [result_b],
        }
    )
    llm = FakeLLM(
        answer=(
            '{"answer":"Les deux documents ont en commun le suivi '
            'd activites au moyen d indicateurs.",'
            '"used_sources":["SOURCE_1","SOURCE_2"]}'
        )
    )
    pipeline = RAGPipeline(
        embedding_service=embedding_service,
        vector_store=vector_store,
        prompt_builder=PromptBuilder(),
        llm=llm,
        config=RAGConfig(),
    )

    response = pipeline.answer(
        "y a t il un lien en commun entre ces documents ?",
        document_ids=["doc-a", "doc-b"],
    )

    assert response.answer != RAGPipeline.NO_RESULTS_MESSAGE
    assert response.answer == (
        "Les deux documents ont en commun le suivi d activites au moyen "
        "d indicateurs."
    )
    assert {source.document_id for source in response.sources} == {
        "doc-a",
        "doc-b",
    }
    assert "final.pdf" in llm.received_prompts[0]
    assert "Environnement.docx" in llm.received_prompts[0]


def test_comparative_retrieval_merge_deduplicates_chunk_ids():
    result_a = create_result(
        text="Information détaillée A. " + "A" * 120,
        document_id="doc-a",
        chunk_id="chunk-a",
    )
    result_b = create_result(
        text="Information détaillée B. " + "B" * 120,
        document_id="doc-b",
        chunk_id="chunk-b",
    )
    pipeline, _, _, prompt_builder, _ = create_pipeline(
        results_by_document_ids={
            ("doc-a", "doc-b"): [result_a],
            ("doc-b",): [result_b, result_b],
        }
    )

    pipeline.answer(
        "Compare ces deux documents.",
        document_ids=["doc-a", "doc-b"],
    )

    selected_chunk_ids = [
        result.chunk_id
        for result in prompt_builder.received_results[0]
    ]
    assert selected_chunk_ids.count("chunk-b") == 1


def test_comparative_question_without_one_document_stops_before_llm():
    result_a = create_result(
        text="Information détaillée A. " + "A" * 120,
        document_id="doc-a",
        chunk_id="chunk-a",
    )
    pipeline, _, vector_store, prompt_builder, llm = create_pipeline(
        results_by_document_ids={
            ("doc-a", "doc-b"): [result_a],
            ("doc-b",): [],
        }
    )

    response = pipeline.answer(
        "Quelles différences entre ces documents ?",
        document_ids=["doc-a", "doc-b"],
    )

    assert response.answer == RAGPipeline.NO_RESULTS_MESSAGE
    assert response.sources == []
    assert vector_store.received_document_ids == [
        ("doc-a", "doc-b"),
        ("doc-b",),
    ]
    assert prompt_builder.received_results == []
    assert llm.received_prompts == []


def test_normal_question_can_answer_when_one_selected_document_has_no_result():
    result_a = create_result(
        text="Information détaillée A. " + "A" * 120,
        document_id="doc-a",
        chunk_id="chunk-a",
    )
    pipeline, _, vector_store, prompt_builder, llm = create_pipeline(
        results=[result_a]
    )

    response = pipeline.answer(
        "Que dit le premier document ?",
        document_ids=["doc-a", "doc-b"],
    )

    assert response.answer == "Réponse générée."
    assert vector_store.received_document_ids == [("doc-a", "doc-b")]
    assert prompt_builder.received_results == [[result_a]]
    assert llm.received_prompts == [prompt_builder.prompt]


def test_comparative_question_does_not_inject_history_into_retrieval_query():
    results = [
        create_result(
            text="Information détaillée A. " + "A" * 120,
            document_id="doc-a",
            chunk_id="chunk-a",
        ),
        create_result(
            text="Information détaillée B. " + "B" * 120,
            document_id="doc-b",
            chunk_id="chunk-b",
        ),
    ]
    pipeline, embedding_service, _, prompt_builder, _ = create_pipeline(
        results=results
    )
    history = [
        {"role": "user", "content": "Ancienne question sur les outils"},
        {"role": "assistant", "content": "Ancienne réponse"},
    ]
    question = "Y a-t-il un point commun entre ces documents ?"

    pipeline.answer(
        question,
        document_ids=["doc-a", "doc-b"],
        conversation_history=history,
    )

    assert embedding_service.received_questions == [question]
    assert prompt_builder.received_histories == [history]


@pytest.mark.parametrize(
    "question",
    [
        "Quel est leur point commun ?",
        "Ont-ils un lien en commun ?",
        "Quelle est leur différence ?",
        "Compare les rapports.",
        "Quel rapport existe entre ces documents ?",
        "Analyse ces deux documents.",
    ],
)
def test_comparative_question_detection(question):
    assert RAGPipeline._is_comparative_question(
        question,
        ("doc-a", "doc-b"),
    )
    assert not RAGPipeline._is_comparative_question(
        question,
        ("doc-a",),
    )


def test_regression_comparative_retrieval_covers_final_and_environment():
    final_results = [
        create_result(
            text=f"Passage final {index}. " + "A" * 120,
            document_name="final.pdf",
            document_id="final-id",
            chunk_id=f"final-chunk-{index}",
        )
        for index in range(20)
    ]
    environment_results = [
        create_result(
            text=f"Passage environnement {index}. " + "B" * 120,
            document_name="Environnement.docx",
            document_id="environment-id",
            chunk_id=f"environment-chunk-{index}",
        )
        for index in range(3)
    ]
    pipeline, _, vector_store, prompt_builder, _ = create_pipeline(
        results_by_document_ids={
            ("final-id", "environment-id"): final_results,
            ("environment-id",): environment_results,
        },
        top_k=10,
    )

    pipeline.answer(
        "y a t il un lien en commun entre ces documents ?",
        document_ids=["final-id", "environment-id"],
    )

    assert vector_store.received_document_ids == [
        ("final-id", "environment-id"),
        ("environment-id",),
    ]
    selected_results = prompt_builder.received_results[0]
    assert {result.document_name for result in selected_results} == {
        "final.pdf",
        "Environnement.docx",
    }


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
        llm_answer=(
            '{"answer":"Le contrat dure trois mois.",'
            '"used_sources":["SOURCE_1"]}'
        ),
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
        results=[result],
        llm_answer=(
            '{"answer":"Le contrat dure trois mois.",'
            '"used_sources":["SOURCE_1"]}'
        ),
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
    assert source.excerpt == result.text
    assert source.distance == 0.05


def test_only_one_used_source_is_returned_from_ten_candidates():
    results = [
        create_result(
            text=f"Candidate passage {index}. " + "A" * 120,
            page_number=index,
            chunk_id=f"chunk-{index}",
        )
        for index in range(1, 11)
    ]
    pipeline, *_ = create_pipeline(
        results=results,
        top_k=10,
        llm_answer=(
            '{"answer":"Answer from the third passage.",'
            '"used_sources":["SOURCE_3"]}'
        ),
    )

    response = pipeline.answer("Question")

    assert len(response.sources) == 1
    assert response.sources[0].excerpt == results[2].text


def test_multiple_used_sources_preserve_model_order():
    results = [
        create_result(
            text=f"Candidate passage {index}. " + "A" * 120,
            page_number=index,
            chunk_id=f"chunk-{index}",
        )
        for index in range(1, 6)
    ]
    pipeline, *_ = create_pipeline(
        results=results,
        top_k=5,
        llm_answer=(
            '{"answer":"Combined answer.",'
            '"used_sources":["SOURCE_2","SOURCE_5"]}'
        ),
    )

    response = pipeline.answer("Question")

    assert [source.excerpt for source in response.sources] == [
        results[1].text,
        results[4].text,
    ]


def test_fallback_answer_always_has_no_sources():
    pipeline, *_ = create_pipeline(
        results=[create_result()],
        llm_answer=(
            '{"answer":"Information non disponible dans les documents.",'
            '"used_sources":["SOURCE_1"]}'
        ),
    )

    assert pipeline.answer("Question").sources == []


def test_unknown_source_id_is_ignored():
    pipeline, *_ = create_pipeline(
        results=[create_result()],
        llm_answer=(
            '{"answer":"Answer.",'
            '"used_sources":["SOURCE_999"]}'
        ),
    )

    assert pipeline.answer("Question").sources == []


def test_non_json_generation_is_returned_without_source_ids():
    answer, used_source_ids = RAGPipeline._parse_generation(
        "Normal answer without JSON"
    )


    assert answer == "Normal answer without JSON"
    assert used_source_ids is None


def test_non_json_generation_with_braces_is_returned_as_user_text():
    generated_content = "La formule est f(x) = {x + 1}."

    answer, used_source_ids = RAGPipeline._parse_generation(
        generated_content
    )

    assert answer == generated_content
    assert used_source_ids is None


def test_truncated_json_recovers_answer_and_decodes_escapes():
    generated_content = (
        '{"answer":"Bonjour\\n\\nVoici \\"les\\" informations\\timportantes 😀. '
        'Chemin: C:\\\\docs", "used_sources":["SOURCE_1"'
    )

    answer, used_source_ids = RAGPipeline._parse_generation(
        generated_content
    )

    assert answer == (
        'Bonjour\n\nVoici "les" informations\timportantes 😀. Chemin: C:\\docs'
    )
    assert used_source_ids == ["SOURCE_1"]


def test_truncated_json_recovers_and_normalizes_source_ids():
    generated_content = (
        'Préambule ```json\n{"answer":"Réponse publique.",'
        '"used_sources":["SOURCE_1","source_2","SOURCE_1",'
        '"autre","SOURCE_X","SOURCE_3'
    )

    answer, used_source_ids = RAGPipeline._parse_generation(
        generated_content
    )

    assert answer == "Réponse publique."
    assert used_source_ids == ["SOURCE_1", "SOURCE_2", "SOURCE_3"]


def test_truncated_sources_ignore_unquoted_protocol_ids():
    answer, used_source_ids = RAGPipeline._parse_generation(
        '{"answer":"Réponse publique.","used_sources":[SOURCE_1'
    )

    assert answer == "Réponse publique."
    assert used_source_ids is None


def test_missing_answer_quote_stops_before_used_sources_field():
    answer, used_source_ids = RAGPipeline._parse_generation(
        '{"answer":"Réponse publique, "used_sources":["SOURCE_1"'
    )

    assert answer == "Réponse publique"
    assert used_source_ids == ["SOURCE_1"]


def test_truncated_answer_without_sources_returns_none_for_source_ids():
    answer, used_source_ids = RAGPipeline._parse_generation(
        '{"answer":"Réponse encore utilisable malgré la coupure'
    )

    assert answer == "Réponse encore utilisable malgré la coupure"
    assert used_source_ids is None


def test_unrecoverable_internal_protocol_is_never_returned():
    generated_content = '{"used_sources":["SOURCE_1"'

    answer, used_source_ids = RAGPipeline._parse_generation(
        generated_content
    )

    assert answer == RAGPipeline.NO_RESULTS_MESSAGE
    assert used_source_ids == []
    assert generated_content not in answer


def test_duplicate_source_ids_are_returned_once():
    pipeline, *_ = create_pipeline(
        results=[create_result()],
        llm_answer=(
            '{"answer":"Answer.",'
            '"used_sources":["SOURCE_1","SOURCE_1"]}'
        ),
    )

    assert len(pipeline.answer("Question").sources) == 1


def test_json_inside_markdown_fence_is_parsed():
    pipeline, *_ = create_pipeline(
        results=[create_result()],
        llm_answer=(
            '```json\n{"answer":"Answer.",'
            '"used_sources":["SOURCE_1"]}\n```'
        ),
    )

    response = pipeline.answer("Question")

    assert response.answer == "Answer."
    assert len(response.sources) == 1


def test_parser_preserves_french_amount_in_arabic_answer():
    answer, used_source_ids = RAGPipeline._parse_generation(
        '{"answer":"الراتب الشهري هو 9 500 dirhams.",'
        '"used_sources":["SOURCE_1"]}'
    )

    assert answer == "الراتب الشهري هو 9 500 dirhams."
    assert used_source_ids == ["SOURCE_1"]


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


def test_no_results_uses_arabic_fallback_for_arabic_question():
    pipeline, _, _, _, llm = create_pipeline(results=[])

    response = pipeline.answer("ما مدة العقد؟")

    assert response.answer == "المعلومة غير متوفرة في الوثائق."
    assert response.sources == []
    assert llm.received_prompts == []


def test_french_model_fallback_is_normalized_to_arabic_for_arabic_question():
    pipeline, *_ = create_pipeline(
        results=[create_result()],
        llm_answer=(
            '{"answer":"Information non disponible dans les documents.",'
            '"used_sources":["SOURCE_1"]}'
        ),
    )

    response = pipeline.answer("ما مدة العقد؟")

    assert response.answer == "المعلومة غير متوفرة في الوثائق."
    assert response.sources == []


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
            document_ids=None,
            filters=None,
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
