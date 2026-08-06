from pathlib import Path

from app.vectorstore.chroma_store import ChromaStore
from app.vectorstore.config import VectorStoreConfig


def test_chroma_store_initialization():
    config = VectorStoreConfig(
        persist_directory=Path("tests/chroma_db"),
        collection_name="test_collection",
    )

    store = ChromaStore(config)

    assert store._client is not None
    assert store._collection is not None
    assert config.persist_directory.exists()