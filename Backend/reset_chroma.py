import os
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.vectorstore.chroma_store import ChromaStore
from app.vectorstore.config import VectorStoreConfig


def main() -> None:
    host = os.getenv("CHROMA_HOST", "localhost")
    port = int(os.getenv("CHROMA_PORT", "8001"))
    collection_name = "documents"

    store = ChromaStore(
        config=VectorStoreConfig(
            host=host,
            port=port,
            collection_name=collection_name,
        )
    )

    try:
        chunk_count = store.count()

        print("ATTENTION : cette opération supprimera tous les chunks ciblés.")
        print("CHROMA_HOST :", host)
        print("CHROMA_PORT :", port)
        print("Collection  :", collection_name)
        print("Chunks actuels :", chunk_count)

        confirmation = input(
            'Saisissez exactement "RESET" pour confirmer : '
        )
        if confirmation != "RESET":
            print("Reset annulé. Chroma n'a pas été modifié.")
            return

        store.clear()
        print("Reset effectué. Chunks après :", store.count())
    finally:
        store.close()


if __name__ == "__main__":
    main()
