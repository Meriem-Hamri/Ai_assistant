import os
from uuid import uuid4

# La suite doit utiliser le modèle BGE-M3 déjà présent dans le cache local.
os.environ["HF_HUB_OFFLINE"] = "1"

import pytest
from chromadb import EphemeralClient

from app.embeddings.embedding_service import EmbeddingService


@pytest.fixture(scope="session")
def embedding_service():
    """
    Crée une seule instance du service d'embedding
    pour toute la session de tests.
    """
    return EmbeddingService()

from app.vectorstore.chroma_store import ChromaStore
from app.vectorstore.config import VectorStoreConfig


@pytest.fixture
def store():
    """
    Crée un ChromaStore propre pour chaque test.
    """

    client = EphemeralClient()
    config = VectorStoreConfig(
        host="localhost",
        port=8001,
        collection_name=f"test_collection_{uuid4().hex}",
    )

    store = ChromaStore(config, client=client)

    yield store

    client.delete_collection(config.collection_name)
    store.close()
