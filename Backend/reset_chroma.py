import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.vectorstore.chroma_store import ChromaStore
from app.vectorstore.config import VectorStoreConfig


store = ChromaStore(
    config=VectorStoreConfig(
        persist_directory=BACKEND_DIR / "data" / "chroma",
        collection_name="documents",
    )
)

print("Chunks avant :", store.count())

store.clear()

print("Chunks après :", store.count())
