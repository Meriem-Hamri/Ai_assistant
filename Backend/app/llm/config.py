from dataclasses import dataclass


@dataclass(frozen=True)
class LLMConfig:
    """
    Configuration utilisée pour le modèle de langage.
    """

    # Qwen2.5 n'active pas de longue trace de raisonnement et est nettement
    # plus adapté à une exécution CPU locale avec 16 Go de RAM.
    model: str = "qwen3:4b-instruct"

    temperature: float = 0.0

    # Les réponses RAG sont concises. Cette limite évite qu'un modèle local
    # monopolise le CPU en générant inutilement de longues réponses.
    max_tokens: int = 512

    top_p: float = 0.9

    top_k: int = 40

    repeat_penalty: float = 1.1

    # Qwen3 peut produire une longue trace de raisonnement. L'appelant peut
    # l'activer explicitement si un cas d'usage le justifie.
    think: bool = False

    stream: bool = False
