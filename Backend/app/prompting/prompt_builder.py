from app.prompting.config import PromptConfig
from app.prompting.templates import (
    ANSWER_HEADER,
    CONTEXT_HEADER,
    PROMPT_TEMPLATE,
    QUESTION_HEADER,
)
from app.prompting.utils import build_context
from app.vectorstore.search_result import SearchResult


CITATION_OUTPUT_INSTRUCTION = (
    "Retourne uniquement un objet JSON valide avec exactement deux champs : "
    "'answer', contenant la reponse destinee a l'utilisateur, et "
    "'used_sources', contenant la liste des identifiants SOURCE_N des seuls "
    "passages qui soutiennent effectivement la reponse. "
    "N'inclus jamais un passage seulement parce qu'il apparait dans le contexte. "
    "Si l'information n'est pas disponible, utilise la reponse de fallback "
    "dans 'answer' et une liste 'used_sources' vide. "
    "Format exact : {\"answer\": \"...\", "
    "\"used_sources\": [\"SOURCE_1\"]}. "
    "N'ajoute ni bloc Markdown, ni commentaire, ni raisonnement."
)


class PromptBuilder:
    """
    Construit le prompt envoyé au modèle de langage
    à partir d'une question et des résultats du Vector Store.
    """

    def __init__(self, config: PromptConfig | None = None) -> None:
        """
        Initialise le Prompt Builder.

        Args:
            config: Configuration du Prompt Builder.
                   Une configuration par défaut est utilisée
                   si aucune configuration n'est fournie.
        """

        self._config = config or PromptConfig()

    def build(
        self,
        question: str,
        results: list[SearchResult],
    ) -> str:
        """
        Construit le prompt final destiné au LLM.

        Args:
            question: Question posée par l'utilisateur.
            results: Résultats provenant du Vector Store.

        Returns:
            Prompt final sous forme de chaîne de caractères.
        """

        if not question or not question.strip():
            raise ValueError(
                "La question ne peut pas être vide."
            )

        context = build_context(
            results=results,
            max_results=self._config.max_results,
            max_context_length=self._config.max_context_length,
            include_metadata=self._config.include_source_metadata,
        )

        return PROMPT_TEMPLATE.format(
            system_instruction=(
                f"{self._config.system_instruction} "
                f"{CITATION_OUTPUT_INSTRUCTION}"
            ),
            context_header=CONTEXT_HEADER,
            context=context,
            question_header=QUESTION_HEADER,
            question=question.strip(),
            answer_header=ANSWER_HEADER,
        )
