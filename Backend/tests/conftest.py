import os

# La suite doit utiliser le modèle BGE-M3 déjà présent dans le cache local.
os.environ["HF_HUB_OFFLINE"] = "1"

import pytest

from app.embeddings.embedding_service import EmbeddingService


@pytest.fixture(scope="session")
def embedding_service():
    """
    Crée une seule instance du service d'embedding
    pour toute la session de tests.
    """
    return EmbeddingService()

import shutil
from pathlib import Path

import pytest
import gc
from app.vectorstore.chroma_store import ChromaStore
from app.vectorstore.config import VectorStoreConfig


TEST_DB = Path("tests/chroma_db")


@pytest.fixture
def store():
    """
    Crée un ChromaStore propre pour chaque test.
    """

    config = VectorStoreConfig(
        persist_directory=TEST_DB,
        collection_name="test_collection",
    )

    store = ChromaStore(config)

    yield store

    store.clear()
    store.close()

    gc.collect()
