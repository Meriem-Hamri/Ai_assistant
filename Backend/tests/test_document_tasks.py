import os
from dataclasses import replace
from pathlib import Path

import pytest

from app.documents.processing_input import DocumentProcessingInput
from app.documents.processor import DocumentProcessingResult


os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.tasks import documents as document_tasks


class FakeRepository:
    def __init__(
        self,
        document: DocumentProcessingInput | None,
        *,
        update_error: Exception | None = None,
    ) -> None:
        self.document = document
        self.update_error = update_error
        self.updates: list[dict] = []

    def get_for_processing(self, document_id: str):
        return self.document

    def update(self, document_id: str, updates: dict) -> bool:
        self.updates.append(dict(updates))
        if self.update_error is not None and updates["status"] == "ready":
            raise self.update_error
        return True


class FakeProcessor:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[dict] = []

    def process(self, **kwargs) -> DocumentProcessingResult:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return DocumentProcessingResult(
            page_count=4,
            chunk_count=9,
            title="Titre final",
            category="Finance",
            year=2026,
            person="Nadia",
            department="Audit",
            document_type="Rapport",
            tags=["final"],
        )


def make_document(file_path: Path, **overrides) -> DocumentProcessingInput:
    document = DocumentProcessingInput(
        id="document-id",
        filename="rapport.pdf",
        path=str(file_path),
        status="queued",
        title="Titre manuel",
        category="Juridique",
        year=2025,
        person="Amine",
        department="Direction",
        document_type="Contrat",
        tags=None,
        ocr_language="ar",
    )
    return replace(document, **overrides)


def install_dependencies(monkeypatch, repository, processor):
    monkeypatch.setattr(
        document_tasks,
        "get_document_repository",
        lambda: repository,
    )
    monkeypatch.setattr(
        document_tasks,
        "create_document_processor",
        lambda: processor,
    )


def test_missing_document_is_ignored(monkeypatch):
    repository = FakeRepository(None)
    processor = FakeProcessor()
    install_dependencies(monkeypatch, repository, processor)

    document_tasks.process_document("missing-id")

    assert repository.updates == []
    assert processor.calls == []


@pytest.mark.parametrize("status", ["processing", "ready", "error"])
def test_non_queued_document_is_ignored(monkeypatch, tmp_path: Path, status: str):
    repository = FakeRepository(make_document(tmp_path / "doc.pdf", status=status))
    processor = FakeProcessor()
    install_dependencies(monkeypatch, repository, processor)

    document_tasks.process_document("document-id")

    assert repository.updates == []
    assert processor.calls == []


@pytest.mark.parametrize(
    ("stored_tags", "expected_provided", "expected_tags"),
    [
        (None, False, []),
        ([], True, []),
        (["audit"], True, ["audit"]),
    ],
)
def test_queued_document_transitions_to_ready_and_rebuilds_metadata(
    monkeypatch,
    tmp_path: Path,
    stored_tags,
    expected_provided,
    expected_tags,
):
    file_path = tmp_path / "doc.pdf"
    file_path.touch()
    repository = FakeRepository(make_document(file_path, tags=stored_tags))
    processor = FakeProcessor()
    install_dependencies(monkeypatch, repository, processor)

    document_tasks.process_document("document-id")

    assert [update["status"] for update in repository.updates] == [
        "processing",
        "ready",
    ]
    assert processor.calls == [
        {
            "file_path": file_path,
            "document_id": "document-id",
            "filename": "rapport.pdf",
            "manual_metadata": {
                "title": "Titre manuel",
                "category": "Juridique",
                "year": 2025,
                "person": "Amine",
                "department": "Direction",
                "document_type": "Contrat",
                "tags": expected_tags,
            },
            "manual_tags_provided": expected_provided,
            "reference_values": {
                "category": ["Finance", "Ressources humaines", "Informatique", "Juridique", "Commercial", "Marketing", "Formation", "Administration", "Opérations"],
                "department": ["Direction générale", "Finance", "Ressources humaines", "Informatique", "Commercial", "Marketing", "Juridique", "Opérations"],
                "document_type": ["Rapport", "Contrat", "Procédure", "Guide", "Facture", "Présentation", "CV", "Note", "Politique"],
            },
            "ocr_language": "ar",
        }
    ]
    assert repository.updates[-1] == {
        "status": "ready",
        "error_message": None,
        "page_count": 4,
        "chunk_count": 9,
        "title": "Titre final",
        "category": "Finance",
        "year": 2026,
        "person": "Nadia",
        "department": "Audit",
        "document_type": "Rapport",
        "tags": ["final"],
    }


def test_missing_file_sets_error(monkeypatch, tmp_path: Path):
    repository = FakeRepository(make_document(tmp_path / "missing.pdf"))
    processor = FakeProcessor()
    install_dependencies(monkeypatch, repository, processor)

    with pytest.raises(FileNotFoundError):
        document_tasks.process_document("document-id")

    assert [update["status"] for update in repository.updates] == [
        "processing",
        "error",
    ]
    assert repository.updates[-1]["error_message"] == (
        "Le traitement du document a échoué."
    )
    assert processor.calls == []


def test_processor_error_sets_generic_error_and_preserves_original_exception(
    monkeypatch,
    tmp_path: Path,
):
    file_path = tmp_path / "doc.pdf"
    file_path.touch()
    repository = FakeRepository(make_document(file_path))
    processor = FakeProcessor(error=ValueError("détail technique"))
    install_dependencies(monkeypatch, repository, processor)

    with pytest.raises(ValueError, match="détail technique"):
        document_tasks.process_document("document-id")

    assert [update["status"] for update in repository.updates] == [
        "processing",
        "error",
    ]
    assert repository.updates[-1] == {
        "status": "error",
        "error_message": "Le traitement du document a échoué.",
    }
