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

results = store._collection.get(
    include=["metadatas"]
)

metadatas = results["metadatas"]

document_ids = {}

for metadata in metadatas:
    document_id = metadata.get("document_id")
    document_name = metadata.get("document_name")

    if document_id not in document_ids:
        document_ids[document_id] = {
            "document_name": document_name,
            "chunks": 0,
        }

    document_ids[document_id]["chunks"] += 1


print("\n=== DOCUMENTS PRESENTS DANS CHROMA ===\n")

for document_id, info in document_ids.items():
    print(f"ID       : {document_id}")
    print(f"Nom      : {info['document_name']}")
    print(f"Chunks   : {info['chunks']}")
    print("-" * 60)

print(f"\nNombre total de documents dans Chroma : {len(document_ids)}")
print(f"Nombre total de chunks                : {len(metadatas)}")
