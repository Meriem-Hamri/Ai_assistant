import pytest

from app.documents.service import DocumentService
from app.models.document import Document, DocumentPage
from app.chunking.natural_chunker import NaturalChunker
from app.vectorstore.utils import prepare_chroma_payload


def test_normalizes_business_metadata():
    metadata = DocumentService._build_business_metadata(
        title=" Contrat de travail ",
        category=" Finance ",
        year=2016,
        person=" Ahmed ",
        department=" RH ",
        document_type=" Contrat ",
        tags=[" salaire ", "contrat", "salaire", ""],
    )

    assert metadata == {
        "title": "Contrat de travail",
        "category": "Finance",
        "year": 2016,
        "person": "Ahmed",
        "department": "RH",
        "document_type": "Contrat",
        "tags": ["salaire", "contrat"],
    }


def test_rejects_invalid_metadata_year():
    with pytest.raises(ValueError, match="année"):
        DocumentService._build_business_metadata(
            title=None,
            category=None,
            year=999,
            person=None,
            department=None,
            document_type=None,
            tags=None,
        )


def test_propagates_document_metadata_to_chroma_chunks():
    document = Document(
        filename="contrat_2016.pdf",
        id="document-1",
        pages=[DocumentPage(page_number=1, text="Le salaire mensuel est de 9500 DH.")],
        metadata={
            "category": "finance",
            "year": 2016,
            "person": "Ahmed",
            "tags": ["rémunération", "salaire"],
        },
    )

    chunk = NaturalChunker(min_chunk_size=1).chunk(document)[0]
    _, _, _, metadatas = prepare_chroma_payload(
        [chunk],
        [[0.1, 0.2]],
    )

    assert chunk.metadata == document.metadata
    assert metadatas[0]["category"] == "finance"
    assert metadatas[0]["year"] == 2016
    assert metadatas[0]["person"] == "Ahmed"
    assert metadatas[0]["tags"] == "rémunération, salaire"
    assert metadatas[0]["tag_salaire"] is True
