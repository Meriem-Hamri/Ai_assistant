import pytest

from app.embeddings.embedding_service import EmbeddingService


@pytest.fixture(scope="session")
def embedding_service():
    """
    Crée une seule instance du service d'embedding
    pour toute la session de tests.
    """
    return EmbeddingService()
