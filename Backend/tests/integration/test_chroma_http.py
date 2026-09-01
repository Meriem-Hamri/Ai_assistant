import os
from contextlib import suppress
from uuid import uuid4

import pytest
from chromadb import HttpClient
from chromadb.errors import NotFoundError

from app.models.document import Chunk
from app.vectorstore.chroma_store import ChromaStore
from app.vectorstore.config import VectorStoreConfig


pytestmark = pytest.mark.integration


def test_chroma_http_add_query_delete():
    if os.getenv("RUN_CHROMA_HTTP_INTEGRATION") != "1":
        pytest.skip("set RUN_CHROMA_HTTP_INTEGRATION=1 to test Chroma Server")

    config = VectorStoreConfig(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", "8001")),
        collection_name=f"integration_{uuid4().hex}",
    )
    client = HttpClient(host=config.host, port=config.port)
    store = None

    try:
        store = ChromaStore(config=config)
        chunk = Chunk(
            text="Test d'integration Chroma HTTP.",
            document_id="integration-document",
            document_name="integration.txt",
            page_number=1,
            chunk_index=0,
            start_char=0,
            end_char=31,
        )
        embedding = [0.1] * 8

        store.add_chunks([chunk], [embedding])
        assert store.count() == 1

        results = store.search(embedding=embedding, top_k=1)
        assert [result.document_id for result in results] == [
            "integration-document"
        ]

        store.delete_document("integration-document")
        assert store.count() == 0
    finally:
        try:
            with suppress(NotFoundError):
                client.delete_collection(config.collection_name)
        finally:
            if store is not None:
                store.close()
