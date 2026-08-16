from unittest.mock import patch

import pytest

from app.llm.config import LLMConfig
from app.llm.qwen_client import QwenClient


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeResponse:
    def __init__(self, content: str) -> None:
        self.message = FakeMessage(content)


def test_qwen_client_uses_default_config():
    """
    Vérifie que le client utilise une configuration
    par défaut lorsqu'aucune configuration n'est fournie.
    """

    client = QwenClient()

    assert client._config == LLMConfig()


def test_qwen_client_uses_custom_config():
    """
    Vérifie qu'une configuration personnalisée est utilisée.
    """

    config = LLMConfig(
        model="qwen3:4b",
        temperature=0.2,
        max_tokens=1024,
        top_p=0.95,
        top_k=50,
        repeat_penalty=1.2,
    )

    client = QwenClient(config)

    assert client._config == config


def test_generate_rejects_empty_prompt():
    """
    Vérifie qu'un prompt vide est refusé.
    """

    client = QwenClient()

    with pytest.raises(ValueError):
        client.generate("")


def test_generate_rejects_whitespace_prompt():
    """
    Vérifie qu'un prompt contenant uniquement des espaces
    est refusé.
    """

    client = QwenClient()

    with pytest.raises(ValueError):
        client.generate("   ")


@patch("app.llm.qwen_client.chat")
def test_generate_returns_response(mock_chat):
    """
    Vérifie que generate() retourne correctement
    la réponse du modèle.
    """

    mock_chat.return_value = FakeResponse(
        "Voici la réponse générée."
    )

    client = QwenClient()

    result = client.generate("Quelle est la question ?")

    assert result == "Voici la réponse générée."

    mock_chat.assert_called_once()


@patch("app.llm.qwen_client.chat")
def test_generate_sends_correct_model(mock_chat):
    """
    Vérifie que le modèle configuré est envoyé à Ollama.
    """

    mock_chat.return_value = FakeResponse("Réponse")

    config = LLMConfig(
        model="qwen3:4b",
    )

    client = QwenClient(config)

    client.generate("Test")

    _, kwargs = mock_chat.call_args

    assert kwargs["model"] == "qwen3:4b"


@patch("app.llm.qwen_client.chat")
def test_generate_sends_prompt(mock_chat):
    """
    Vérifie que le prompt est envoyé comme message utilisateur.
    """

    mock_chat.return_value = FakeResponse("Réponse")

    client = QwenClient()

    client.generate("  Bonjour Qwen  ")

    _, kwargs = mock_chat.call_args

    assert kwargs["messages"] == [
        {
            "role": "user",
            "content": "Bonjour Qwen",
        }
    ]


@patch("app.llm.qwen_client.chat")
def test_generate_sends_generation_options(mock_chat):
    """
    Vérifie que les paramètres de génération
    sont transmis correctement à Ollama.
    """

    mock_chat.return_value = FakeResponse("Réponse")

    config = LLMConfig(
        temperature=0.2,
        max_tokens=1024,
        top_p=0.95,
        top_k=50,
        repeat_penalty=1.2,
    )

    client = QwenClient(config)

    client.generate("Test")

    _, kwargs = mock_chat.call_args

    assert kwargs["options"] == {
        "temperature": 0.2,
        "num_predict": 1024,
        "top_p": 0.95,
        "top_k": 50,
        "repeat_penalty": 1.2,
    }