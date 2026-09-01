from pathlib import Path

import pytest

from app.documents.processor import DocumentProcessingResult, DocumentProcessor
from app.models.document import Document, DocumentPage


AUTOMATIC_METADATA = {
    "title": "Titre automatique",
    "category": "Finance",
    "year": 2025,
    "person": "Amine",
    "department": "Comptabilité",
    "document_type": "Rapport",
    "tags": ["budget", "finance"],
}


def manual_metadata(**overrides) -> dict:
    metadata = {
        "title": None,
        "category": None,
        "year": None,
        "person": None,
        "department": None,
        "document_type": None,
        "tags": [],
    }
    metadata.update(overrides)
    return metadata


class FakeExtractedMetadata:
    def to_dict(self) -> dict:
        return dict(AUTOMATIC_METADATA)


class FakeMetadataExtractor:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def extract(self, text: str) -> FakeExtractedMetadata:
        self.texts.append(text)
        return FakeExtractedMetadata()


class FakeIndexer:
    def __init__(self) -> None:
        self.documents: list[Document] = []

    def index(self, document: Document) -> list[object]:
        self.documents.append(document)
        return [object(), object(), object()]


def test_process_runs_pipeline_and_preserves_automatic_tags(
    monkeypatch,
    tmp_path: Path,
):
    source_document = Document(
        filename="stored.pdf",
        pages=[
            DocumentPage(page_number=1, text="  Première page  "),
            DocumentPage(page_number=2, text="  Deuxième page  "),
        ],
    )
    extracted_paths: list[str] = []
    cleaned_texts: list[str] = []

    def fake_extract(file_path: str, ocr_language: str) -> Document:
        extracted_paths.append((file_path, ocr_language))
        return source_document

    def fake_clean(text: str) -> str:
        cleaned_texts.append(text)
        return text.strip()

    monkeypatch.setattr("app.documents.processor.extract_document", fake_extract)
    monkeypatch.setattr("app.documents.processor.clean_document", fake_clean)
    metadata_extractor = FakeMetadataExtractor()
    indexer = FakeIndexer()
    processor = DocumentProcessor(indexer, metadata_extractor)
    file_path = tmp_path / "stored.pdf"

    result = processor.process(
        file_path=file_path,
        document_id="document-id",
        filename="rapport-original.pdf",
        manual_metadata=manual_metadata(title="Titre manuel"),
        manual_tags_provided=False,
        ocr_language="ar",
    )

    assert extracted_paths == [(str(file_path), "ar")]
    assert cleaned_texts == ["  Première page  ", "  Deuxième page  "]
    assert metadata_extractor.texts == ["Première page\n\nDeuxième page"]
    assert indexer.documents == [source_document]
    assert source_document.id == "document-id"
    assert source_document.filename == "rapport-original.pdf"
    assert source_document.metadata == {
        **AUTOMATIC_METADATA,
        "title": "Titre manuel",
    }
    assert result == DocumentProcessingResult(
        page_count=2,
        chunk_count=3,
        title="Titre manuel",
        category="Finance",
        year=2025,
        person="Amine",
        department="Comptabilité",
        document_type="Rapport",
        tags=["budget", "finance"],
    )


def test_process_uses_manual_tags_when_provided(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        "app.documents.processor.extract_document",
        lambda _, __: Document(
            filename="stored.pdf",
            pages=[DocumentPage(page_number=1, text="Texte")],
        ),
    )
    monkeypatch.setattr("app.documents.processor.clean_document", lambda text: text)
    processor = DocumentProcessor(FakeIndexer(), FakeMetadataExtractor())

    result = processor.process(
        file_path=tmp_path / "stored.pdf",
        document_id="document-id",
        filename="rapport.pdf",
        manual_metadata=manual_metadata(tags=["manuel", "prioritaire"]),
        manual_tags_provided=True,
    )

    assert result.tags == ["manuel", "prioritaire"]


def test_process_propagates_pipeline_exception(monkeypatch, tmp_path: Path):
    def fail_extraction(_: str, __: str) -> Document:
        raise RuntimeError("échec extraction")

    monkeypatch.setattr("app.documents.processor.extract_document", fail_extraction)
    indexer = FakeIndexer()
    processor = DocumentProcessor(indexer, FakeMetadataExtractor())

    with pytest.raises(RuntimeError, match="échec extraction"):
        processor.process(
            file_path=tmp_path / "stored.pdf",
            document_id="document-id",
            filename="rapport.pdf",
            manual_metadata=manual_metadata(),
            manual_tags_provided=False,
        )

    assert indexer.documents == []
