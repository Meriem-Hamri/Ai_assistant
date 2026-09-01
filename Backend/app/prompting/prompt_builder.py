from app.prompting.config import PromptConfig
from app.prompting.templates import (
    ANSWER_HEADER,
    CONTEXT_HEADER,
    HISTORY_HEADER,
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


CONVERSATION_HISTORY_INSTRUCTION = (
    "L'historique récent sert uniquement à comprendre la continuité de la "
    "conversation et les références comme 'il', 'elle', 'ils', 'le deuxième'. "
    "Toutes les affirmations factuelles doivent rester fondées sur le contexte "
    "documentaire fourni. L'historique n'est pas une source documentaire."
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
        conversation_history: list[dict[str, str]] | None = None,
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
        history = self._build_history(conversation_history or [])

        return PROMPT_TEMPLATE.format(
            system_instruction=(
                f"{self._config.system_instruction} "
                f"{CONVERSATION_HISTORY_INSTRUCTION} "
                f"{CITATION_OUTPUT_INSTRUCTION}"
            ),
            history_header=HISTORY_HEADER,
            history=history,
            context_header=CONTEXT_HEADER,
            context=context,
            question_header=QUESTION_HEADER,
            question=question.strip(),
            answer_header=ANSWER_HEADER,
        )

    def _build_history(
        self,
        conversation_history: list[dict[str, str]],
    ) -> str:
        """Rend l'historique utile sans entamer le budget documentaire."""

        rendered_messages: list[str] = []
        labels = {"user": "Utilisateur", "assistant": "Assistant"}

        for message in conversation_history:
            role = message.get("role")
            content = message.get("content")
            if role not in labels or not isinstance(content, str):
                continue
            normalized_content = content.strip()
            if normalized_content:
                rendered_messages.append(
                    f"{labels[role]}: {normalized_content}"
                )

        if not rendered_messages:
            return "Aucun historique récent."

        remaining_length = self._config.max_history_length
        selected_messages: list[str] = []

        for rendered_message in reversed(rendered_messages):
            separator_length = 1 if selected_messages else 0
            available_length = remaining_length - separator_length
            if available_length <= 0:
                break
            if len(rendered_message) > available_length:
                if not selected_messages:
                    role_label, _, content = rendered_message.partition(": ")
                    truncated_prefix = f"{role_label}: …"
                    content_length = available_length - len(truncated_prefix)
                    if content_length >= 0:
                        selected_messages.append(
                            f"{truncated_prefix}{content[-content_length:]}"
                            if content_length
                            else truncated_prefix
                        )
                break

            selected_messages.append(rendered_message)
            remaining_length = available_length - len(rendered_message)

        return "\n".join(reversed(selected_messages))
