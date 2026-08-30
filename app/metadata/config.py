from dataclasses import dataclass


@dataclass(frozen=True)
class MetadataExtractorConfig:
    """Configuration de l'analyse locale effectuée à l'import."""

    model: str = "qwen3:4b-instruct"
    max_input_characters: int = 10_000
    max_output_tokens: int = 256
