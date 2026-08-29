from pathlib import Path

from app.vectorstore.chroma_store import ChromaStore
from app.vectorstore.config import VectorStoreConfig


store = ChromaStore(
    config=VectorStoreConfig(
        persist_directory=Path("data/chroma"),
        collection_name="documents",
    )
)

print("Chunks avant :", store.count())

store.clear()

print("Chunks après :", store.count())