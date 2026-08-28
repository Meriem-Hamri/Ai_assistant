def test_initialization(store):
    assert store.count() == 0

from app.models.document import Chunk


def test_add_chunks(store):

    chunk = Chunk(
        text="Paris est la capitale de la France.",
        document_id="doc1",
        document_name="document.pdf",
        page_number=1,
        chunk_index=0,
        start_char=0,
        end_char=34,
    )

    embedding = [0.1] * 1024

    store.add_chunks(
        [chunk],
        [embedding],
    )

    assert store.count() == 1

def test_search(store):

    chunk = Chunk(
        text="Paris est la capitale de la France.",
        document_id="doc1",
        document_name="document.pdf",
        page_number=1,
        chunk_index=0,
        start_char=0,
        end_char=34,
    )

    embedding = [0.1] * 1024

    store.add_chunks(
        [chunk],
        [embedding],
    )

    results = store.search(
        embedding,
        top_k=1,
    )

    assert len(results) == 1

    assert results[0].text == chunk.text

    assert results[0].document_id == chunk.document_id

def test_delete_document(store):

    chunk = Chunk(
        text="Paris est la capitale de la France.",
        document_id="doc1",
        document_name="document.pdf",
        page_number=1,
        chunk_index=0,
        start_char=0,
        end_char=34,
    )

    embedding = [0.1] * 1024

    store.add_chunks(
        [chunk],
        [embedding],
    )

    assert store.count() == 1

    store.delete_document("doc1")

    assert store.count() == 0

def test_clear(store):

    chunk = Chunk(
    text="Paris est la capitale.",
    document_id="doc1",
    document_name="document.pdf",
    page_number=1,
    chunk_index=0,
    start_char=0,
    end_char=24,
)

    embedding = [0.1] * 1024

    store.add_chunks(
        [chunk],
        [embedding],
    )

    assert store.count() == 1

    store.clear()

    assert store.count() == 0

def test_search_empty_collection(store):

    results = store.search(
        [0.1] * 1024
    )

    assert results == []


def test_add_empty_chunks(store):
    store.add_chunks(
        chunks=[],
        embeddings=[],
    )

    assert store.count() == 0

def test_delete_nonexistent_document(store):
    store.delete_document("document_inexistant")

    assert store.count() == 0

def test_delete_only_target_document(store):

    chunk1 = Chunk(
        text="Document A",
        document_id="docA",
        document_name="a.pdf",
        page_number=1,
        chunk_index=0,
        start_char=0,
        end_char=10,
    )

    chunk2 = Chunk(
        text="Document B",
        document_id="docB",
        document_name="b.pdf",
        page_number=1,
        chunk_index=0,
        start_char=0,
        end_char=10,
    )

    embedding = [0.1] * 1024

    store.add_chunks(
        [chunk1, chunk2],
        [embedding, embedding],
    )

    assert store.count() == 2

    store.delete_document("docA")

    assert store.count() == 1

    results = store.search(
        embedding=embedding,
        top_k=5,
    )

    assert all(result.document_id == "docB" for result in results)  

import pytest


def test_search_rejects_empty_embedding(store):
    with pytest.raises(ValueError, match="embedding"):
        store.search(
            embedding=[],
            top_k=5,
        )


def test_search_rejects_non_integer_top_k(store):
    with pytest.raises(TypeError, match="top_k"):
        store.search(
            embedding=[0.1] * 1024,
            top_k=2.5,
        )


def test_search_rejects_zero_top_k(store):
    with pytest.raises(ValueError, match="top_k"):
        store.search(
            embedding=[0.1] * 1024,
            top_k=0,
        )


def test_search_rejects_negative_top_k(store):
    with pytest.raises(ValueError, match="top_k"):
        store.search(
            embedding=[0.1] * 1024,
            top_k=-1,
        )  

def test_search_returns_distance(store):
    chunk = Chunk(
        text="Paris est la capitale de la France.",
        document_id="doc1",
        document_name="document.pdf",
        page_number=1,
        chunk_index=0,
        start_char=0,
        end_char=34,
    )

    embedding = [0.1] * 1024

    store.add_chunks(
        [chunk],
        [embedding],
    )

    results = store.search(
        embedding=embedding,
        top_k=1,
    )

    assert len(results) == 1
    assert isinstance(results[0].distance, float)
    assert results[0].distance >= 0

def test_search_filters_by_max_distance(store):

        chunk = Chunk(
            text="Paris est la capitale de la France.",
            document_id="doc1",
            document_name="document.pdf",
            page_number=1,
            chunk_index=0,
            start_char=0,
            end_char=34,
        )

        embedding = [0.1] * 1024

        store.add_chunks(
            [chunk],
            [embedding],
        )

        results = store.search(
            embedding=embedding,
            top_k=1,
            max_distance=0.1,
        )

        assert len(results) == 1

        assert all(
            result.distance <= 0.1
            for result in results
        )

def test_search_returns_empty_when_all_results_exceed_max_distance(store):

    chunk = Chunk(
        text="Paris est la capitale de la France.",
        document_id="doc1",
        document_name="document.pdf",
        page_number=1,
        chunk_index=0,
        start_char=0,
        end_char=34,
    )

    embedding = [0.1] * 1024
    different_embedding = [0.9] * 1024

    store.add_chunks(
        [chunk],
        [embedding],
    )

    unfiltered_results = store.search(
        embedding=different_embedding,
        top_k=1,
    )

    assert len(unfiltered_results) == 1

    distance = unfiltered_results[0].distance

    results = store.search(
        embedding=different_embedding,
        top_k=1,
        max_distance=distance / 2,
    )

    assert results == []

import pytest


def test_search_rejects_negative_max_distance(store):

    with pytest.raises(ValueError):
        store.search(
            embedding=[0.1] * 1024,
            max_distance=-0.1,
        )

def test_search_rejects_non_numeric_max_distance(store):

    with pytest.raises(TypeError):
        store.search(
            embedding=[0.1] * 1024,
            max_distance="0.5",
        )

def test_search_filters_by_document_id(store):

    chunk1 = Chunk(
        text="Information du document A",
        document_id="docA",
        document_name="a.pdf",
        page_number=1,
        chunk_index=0,
        start_char=0,
        end_char=25,
    )

    chunk2 = Chunk(
        text="Information du document B",
        document_id="docB",
        document_name="b.pdf",
        page_number=1,
        chunk_index=0,
        start_char=0,
        end_char=25,
    )

    embedding = [0.1] * 1024

    store.add_chunks(
        [chunk1, chunk2],
        [embedding, embedding],
    )

    results = store.search(
        embedding=embedding,
        top_k=5,
        document_id="docA",
    )

    assert len(results) == 1
    assert results[0].document_id == "docA"
    assert results[0].text == chunk1.text