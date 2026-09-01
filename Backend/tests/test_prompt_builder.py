import pytest

from app.prompting.config import PromptConfig
from app.prompting.prompt_builder import (
    CITATION_OUTPUT_INSTRUCTION,
    CONVERSATION_HISTORY_INSTRUCTION,
    PromptBuilder,
)
from app.vectorstore.search_result import SearchResult
from app.prompting.language import ARABIC_FALLBACK, FRENCH_FALLBACK


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
        distance=0.05,
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
    assert "Nom du fichier : contrat.pdf" in prompt
    assert "Contenu du passage" in prompt


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
    assert "[SOURCE_1]" in prompt
    assert "[SOURCE_2]" in prompt


def test_prompt_requests_structured_answer_with_used_sources():
    prompt = PromptBuilder().build(
        question="Quelle est la duree ?",
        results=[create_result()],
    )

    assert "objet JSON valide" in prompt
    assert "'answer'" in prompt
    assert "'used_sources'" in prompt


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

    assert "A" * 500 not in prompt
    assert len(prompt) <= (
        len(config.system_instruction)
        + len(CONVERSATION_HISTORY_INSTRUCTION)
        + len(CITATION_OUTPUT_INSTRUCTION)
        + 300
    )


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


def test_prompt_renders_history_in_order_with_role_labels():
    prompt = PromptBuilder().build(
        question="Et pour lui ?",
        results=[create_result(text="Contexte factuel distinct.")],
        conversation_history=[
            {"role": "user", "content": "Parle-moi du premier candidat."},
            {"role": "assistant", "content": "Voici le premier candidat."},
        ],
    )

    user_line = "Utilisateur: Parle-moi du premier candidat."
    assistant_line = "Assistant: Voici le premier candidat."
    assert "HISTORIQUE RÉCENT" in prompt
    assert prompt.index(user_line) < prompt.index(assistant_line)
    assert prompt.index(assistant_line) < prompt.index("CONTEXTE DOCUMENTAIRE")
    assert "Contexte factuel distinct." in prompt
    assert prompt.index("CONTEXTE DOCUMENTAIRE") < prompt.index("QUESTION")
    assert "Et pour lui ?" in prompt
    assert CONVERSATION_HISTORY_INSTRUCTION in prompt


def test_prompt_without_history_keeps_document_context_and_question():
    prompt = PromptBuilder().build(
        question="Question actuelle",
        results=[create_result(text="Contexte documentaire")],
    )

    assert "Aucun historique récent." in prompt
    assert "Contexte documentaire" in prompt
    assert "Question actuelle" in prompt


def test_history_has_dedicated_length_limit():
    max_history_length = 50
    config = PromptConfig(
        max_history_length=max_history_length,
        max_context_length=8000,
    )
    prompt = PromptBuilder(config).build(
        question="Question actuelle",
        results=[create_result(text="DOCUMENT_INTACT")],
        conversation_history=[
            {
                "role": "user",
                "content": (
                    "DEBUT_SUPPRIME_" + "X" * 100 + "_FIN_CONSERVEE"
                ),
            },
        ],
    )
    history_section = prompt.split("HISTORIQUE RÉCENT\n\n", 1)[1].split(
        "\n\nCONTEXTE DOCUMENTAIRE",
        1,
    )[0]

    assert history_section.startswith("Utilisateur: …")
    assert history_section.endswith("_FIN_CONSERVEE")
    assert "DEBUT_SUPPRIME" not in history_section
    assert len(history_section) <= max_history_length
    assert "DOCUMENT_INTACT" in prompt


def test_history_limit_prioritizes_most_recent_messages():
    prompt = PromptBuilder(PromptConfig(max_history_length=45)).build(
        question="Question actuelle",
        results=[create_result()],
        conversation_history=[
            {"role": "user", "content": "A" * 100},
            {"role": "assistant", "content": "Réponse récente"},
        ],
    )
    history_section = prompt.split("HISTORIQUE RÉCENT\n\n", 1)[1].split(
        "\n\nCONTEXTE DOCUMENTAIRE",
        1,
    )[0]

    assert history_section == "Assistant: Réponse récente"


def test_prompt_allows_grounded_comparison_and_forbids_external_facts():
    prompt = PromptBuilder().build(
        question="Quel est le point commun entre ces documents ?",
        results=[create_result()],
    )

    assert "comparer plusieurs documents" in prompt
    assert "identifier leurs points communs et leurs différences" in prompt
    assert "synthétiser plusieurs passages" in prompt
    assert "relation raisonnable directement soutenue par le contexte" in prompt
    assert "déduction logique" in prompt
    assert "aucun fait externe" in prompt
    assert "n'invente aucune information" in prompt
    assert "aucune relation qui n'est pas soutenue" in prompt
    assert "ne permet réellement pas une réponse fondée" in prompt


def test_french_question_with_arabic_result_requests_french_answer():
    prompt = PromptBuilder().build(
        question="Quelle est la durée du contrat ?",
        results=[create_result(text="مدة العقد ثلاثة أشهر.")],
    )

    assert "Réponds en français" in prompt
    assert FRENCH_FALLBACK in prompt
    assert "مدة العقد ثلاثة أشهر." in prompt


def test_arabic_question_with_french_result_requests_arabic_answer():
    prompt = PromptBuilder().build(
        question="ما مدة العقد؟",
        results=[create_result(text="Le contrat dure trois mois.")],
    )

    assert "Réponds en arabe" in prompt
    assert ARABIC_FALLBACK in prompt
    assert "Le contrat dure trois mois." in prompt


def test_arabic_question_requires_exact_french_context_amount():
    prompt = PromptBuilder().build(
        question="ما هو الراتب الشهري؟",
        results=[
            create_result(
                text="Le salaire mensuel brut est fixé à 9 500 dirhams."
            )
        ],
    )

    assert "9 500 dirhams" in prompt
    assert "recopie exactement tous les chiffres" in prompt
    assert "le séparateur et l'unité" in prompt
    assert "FIDÉLITÉ NUMÉRIQUE OBLIGATOIRE" in prompt
    assert prompt.rindex("9 500") < prompt.index("RÉPONSE")
