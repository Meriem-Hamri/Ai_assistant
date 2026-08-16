from dataclasses import dataclass


@dataclass(frozen=True)
class PromptConfig:
    """
    Configuration utilisée pour construire les prompts RAG.
    """

    max_results: int = 5

    max_context_length: int = 8000

    include_source_metadata: bool = True

    system_instruction: str = (
        "Tu es un assistant intelligent spécialisé dans l'analyse "
        "de documents internes. "
        "Réponds uniquement à partir du contexte fourni. "
        "N'invente aucune information. "
        "Si le contexte ne contient pas suffisamment d'informations "
        "pour répondre à la question, indique clairement que "
        "l'information n'est pas disponible dans les documents."
    )