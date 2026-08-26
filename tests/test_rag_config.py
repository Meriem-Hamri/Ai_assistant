import pytest

from app.rag.config import RAGConfig


def test_default_configuration():
    config = RAGConfig()

    assert config.top_k == 5


def test_custom_top_k():
    config = RAGConfig(top_k=10)

    assert config.top_k == 10


def test_top_k_must_be_positive():
    with pytest.raises(ValueError):
        RAGConfig(top_k=0)


def test_negative_top_k_is_rejected():
    with pytest.raises(ValueError):
        RAGConfig(top_k=-1)


def test_top_k_must_be_integer():
    with pytest.raises(TypeError):
        RAGConfig(top_k=5.5)


def test_configuration_is_immutable():
    config = RAGConfig()

    with pytest.raises(AttributeError):
        config.top_k = 10