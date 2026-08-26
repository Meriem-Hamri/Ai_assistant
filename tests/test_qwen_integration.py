from app.llm.qwen_client import QwenClient


def test_qwen_real_generation():
    """
    Teste la génération réelle d'une réponse avec
    Ollama et le modèle Qwen.
    """

    client = QwenClient()

    response = client.generate(
        "Réponds uniquement par : Bonjour"
    )

    assert isinstance(response, str)
    assert response.strip()