from dataclasses import dataclass


@dataclass(frozen=True)
class LLMConfig:
    """
    Configuration utilisée pour le modèle de langage.
    """

    model: str = "qwen3:4b"

    temperature: float = 0.0

    max_tokens: int = 2024

    top_p: float = 0.9

    top_k: int = 40

    repeat_penalty: float = 1.1

    stream: bool = False