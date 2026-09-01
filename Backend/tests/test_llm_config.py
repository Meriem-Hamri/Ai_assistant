from app.llm.config import LLMConfig


def test_default_config():
    """
    Vérifie les valeurs par défaut de la configuration.
    """

    config = LLMConfig()

    assert config.model == "qwen3:4b-instruct"
    assert config.temperature == 0.0
    assert config.max_tokens == 1024
    assert config.top_p == 0.9
    assert config.top_k == 40
    assert config.repeat_penalty == 1.1
    assert config.think is False


def test_custom_config():
    """
    Vérifie qu'une configuration personnalisée peut être créée.
    """

    config = LLMConfig(
        model="qwen3:4b",
        temperature=0.2,
        max_tokens=1024,
        top_p=0.95,
        top_k=50,
        repeat_penalty=1.2,
        think=True,
    )

    assert config.model == "qwen3:4b"
    assert config.temperature == 0.2
    assert config.max_tokens == 1024
    assert config.top_p == 0.95
    assert config.top_k == 50
    assert config.repeat_penalty == 1.2
    assert config.think is True


def test_config_is_immutable():
    """
    Vérifie que la configuration est immuable.
    """

    config = LLMConfig()

    try:
        config.temperature = 0.5
    except AttributeError:
        pass
    else:
        raise AssertionError(
            "LLMConfig devrait être immuable."
        )
