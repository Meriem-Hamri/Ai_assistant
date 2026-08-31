from app.rag.response import RAGResponse, Source


def test_source_creation():
    source = Source(
        document_id="doc-1",
        document_name="contrat.pdf",
        page_number=3,
        chunk_id="chunk-7",
        excerpt="Extrait du contrat.",
        distance=0.12,
    )

    assert source.document_id == "doc-1"
    assert source.document_name == "contrat.pdf"
    assert source.page_number == 3
    assert source.chunk_id == "chunk-7"
    assert source.excerpt == "Extrait du contrat."
    assert source.distance == 0.12


def test_rag_response_creation():
    source = Source(
        document_id="doc-1",
        document_name="contrat.pdf",
        page_number=3,
        chunk_id="chunk-7",
        excerpt="Extrait du contrat.",
        distance=0.12,
    )

    response = RAGResponse(
        answer="Le contrat dure trois mois.",
        sources=[source],
    )

    assert response.answer == "Le contrat dure trois mois."
    assert response.sources == [source]


def test_rag_response_without_sources():
    response = RAGResponse(
        answer="Information non disponible dans les documents.",
        sources=[],
    )

    assert response.answer == (
        "Information non disponible dans les documents."
    )
    assert response.sources == []


def test_source_is_immutable():
    source = Source(
        document_id="doc-1",
        document_name="contrat.pdf",
        page_number=1,
        chunk_id="chunk-1",
        excerpt="Extrait du contrat.",
        distance=0.1,
    )

    try:
        source.distance = 0.2
        assert False, "Source devrait être immuable."
    except AttributeError:
        pass


def test_rag_response_is_immutable():
    response = RAGResponse(
        answer="Réponse",
        sources=[],
    )

    try:
        response.answer = "Nouvelle réponse"
        assert False, "RAGResponse devrait être immuable."
    except AttributeError:
        pass
