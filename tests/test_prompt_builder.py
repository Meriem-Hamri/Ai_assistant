import pytest

from app.prompting.config import PromptConfig
from app.prompting.prompt_builder import PromptBuilder
from app.vectorstore.search_result import SearchResult


def create_result(
    text: str = "Le contrat dure trois mois.",
    document_name: str = "contrat.pdf",
    page_number: int = 1,
) -> SearchResult:
    """
    Crée un SearchResult pour les tests.
    """

    return SearchResult(
        chunk_id="chunk-1",
        text=text,
        score=0.95,
        document_id="doc-1",
        document_name=document_name,
        page_number=page_number,
        chunk_index=0,
        start_char=0,
        end_char=len(text),
    )


def test_build_prompt():
    builder = PromptBuilder()

    results = [
        create_result()
    ]

    prompt = builder.build(
        question="Quelle est la durée du contrat ?",
        results=results,
    )

    assert isinstance(prompt, str)
    assert "Quelle est la durée du contrat ?" in prompt


def test_prompt_contains_context():
    builder = PromptBuilder()

    results = [
        create_result(
            text="Le contrat dure trois mois."
        )
    ]

    prompt = builder.build(
        question="Quelle est la durée du contrat ?",
        results=results,
    )

    assert "Le contrat dure trois mois." in prompt


def test_prompt_contains_source_metadata():
    builder = PromptBuilder()

    results = [
        create_result(
            document_name="contrat.pdf",
            page_number=5,
        )
    ]

    prompt = builder.build(
        question="Quelle est la durée du contrat ?",
        results=results,
    )

    assert "contrat.pdf" in prompt
    assert "5" in prompt


def test_multiple_results():
    builder = PromptBuilder()

    results = [
        create_result(
            text="Premier passage.",
            page_number=1,
        ),
        create_result(
            text="Deuxième passage.",
            page_number=2,
        ),
    ]

    prompt = builder.build(
        question="Que dit le contrat ?",
        results=results,
    )

    assert "Premier passage." in prompt
    assert "Deuxième passage." in prompt
    assert "[Source 1]" in prompt
    assert "[Source 2]" in prompt


def test_empty_results():
    builder = PromptBuilder()

    prompt = builder.build(
        question="Quelle est la durée du contrat ?",
        results=[],
    )

    assert "Aucun passage pertinent" in prompt


def test_empty_question():
    builder = PromptBuilder()

    with pytest.raises(ValueError):
        builder.build(
            question="",
            results=[],
        )


def test_whitespace_question():
    builder = PromptBuilder()

    with pytest.raises(ValueError):
        builder.build(
            question="   ",
            results=[],
        )


def test_max_results():
    config = PromptConfig(
        max_results=2,
    )

    builder = PromptBuilder(config)

    results = [
        create_result(text="Résultat 1"),
        create_result(text="Résultat 2"),
        create_result(text="Résultat 3"),
    ]

    prompt = builder.build(
        question="Question",
        results=results,
    )

    assert "Résultat 1" in prompt
    assert "Résultat 2" in prompt
    assert "Résultat 3" not in prompt


def test_context_length_limit():
    config = PromptConfig(
        max_context_length=50,
    )

    builder = PromptBuilder(config)

    results = [
        create_result(
            text="A" * 500,
        )
    ]

    prompt = builder.build(
        question="Question",
        results=results,
    )

    assert len(prompt) < 1000


def test_custom_configuration():
    config = PromptConfig(
        max_results=1,
        include_source_metadata=False,
    )

    builder = PromptBuilder(config)

    results = [
        create_result(
            text="Information importante.",
            document_name="secret.pdf",
            page_number=10,
        )
    ]

    prompt = builder.build(
        question="Quelle est l'information ?",
        results=results,
    )

    assert "Information importante." in prompt
    assert "secret.pdf" not in prompt