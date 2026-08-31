from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile

from app.api.schemas.document import DocumentResponse
from app.documents.processor import DocumentProcessingResult
from app.documents.service import (
    DocumentDeletionConflictError,
    DocumentService,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


class FakeRepository:
    def __init__(self, *, save_error: Exception | None = None) -> None:
        self.document: dict | None = None
        self.events: list[tuple[str, str]] = []
        self.save_error = save_error

    def save(self, metadata: dict) -> None:
        self.events.append(("save", metadata["status"]))
        if self.save_error is not None:
            raise self.save_error
        self.document = dict(metadata)

    def update(self, document_id: str, updates: dict) -> bool:
        if self.document is None or self.document["id"] != document_id:
            return False
        self.events.append(("update", updates["status"]))
        self.document.update(updates)
        return True

    def get_by_id(self, document_id: str) -> dict | None:
        if self.document is None or self.document["id"] != document_id:
            return None
        return dict(self.document)

    def delete(self, document_id: str) -> bool:
        if self.document is None or self.document["id"] != document_id:
            return False
        self.events.append(("delete", self.document["status"]))
        self.document = None
        return True


class FakeVectorStore:
    def __init__(self) -> None:
        self.deleted_ids: list[str] = []

    def delete_document(self, document_id: str) -> None:
        self.deleted_ids.append(document_id)


class FakeDocumentProcessor:
    def __init__(
        self,
        repository: FakeRepository,
        *,
        error: Exception | None = None,
    ) -> None:
        self.repository = repository
        self.error = error
        self.calls: list[dict] = []

    def process(self, **kwargs) -> DocumentProcessingResult:
        assert self.repository.document is not None
        assert self.repository.document["status"] == "processing"
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return DocumentProcessingResult(
            page_count=1,
            chunk_count=2,
            title="Titre automatique",
            category="Juridique",
            year=2025,
            person="Amine",
            department="Direction",
            document_type="Contrat",
            tags=["contrat"],
        )


def make_service(
    repository: FakeRepository,
    *,
    processor_error: Exception | None = None,
) -> tuple[DocumentService, FakeVectorStore, FakeDocumentProcessor]:
    vector_store = FakeVectorStore()
    processor = FakeDocumentProcessor(repository, error=processor_error)
    return (
        DocumentService(
            processor=processor,
            repository=repository,
            vector_store=vector_store,
        ),
        vector_store,
        processor,
    )


def make_upload() -> UploadFile:
    return UploadFile(filename="rapport.pdf", file=BytesIO(b"contenu"))


@pytest.mark.parametrize("status", ["queued", "processing", "ready", "error"])
def test_document_response_accepts_every_lifecycle_status(status: str):
    response = DocumentResponse.model_validate(
        {
            "id": "document-id",
            "filename": "rapport.pdf",
            "type": "pdf",
            "page_count": None,
            "size": 7,
            "created_at": "2026-08-31T12:00:00Z",
            "status": status,
            "error_message": (
                "Le traitement du document a échoué."
                if status == "error"
                else None
            ),
            "chunk_count": None,
        }
    )

    assert response.status == status
    assert response.page_count is None


@pytest.mark.anyio
async def test_upload_transitions_from_queued_to_processing_to_ready(
    monkeypatch,
    tmp_path: Path,
):
    repository = FakeRepository()
    service, _, processor = make_service(repository)
    monkeypatch.setattr("app.documents.service.DOCUMENTS_DIR", tmp_path)

    result = await service.upload_document(make_upload())

    assert repository.events[:3] == [
        ("save", "queued"),
        ("update", "processing"),
        ("update", "ready"),
    ]
    assert len(processor.calls) == 1
    assert processor.calls[0]["document_id"] == result["id"]
    assert processor.calls[0]["filename"] == "rapport.pdf"
    assert processor.calls[0]["manual_tags_provided"] is False
    assert result["status"] == "ready"
    assert {
        key: result[key]
        for key in (
            "page_count",
            "chunk_count",
            "title",
            "category",
            "year",
            "person",
            "department",
            "document_type",
            "tags",
        )
    } == {
        "page_count": 1,
        "chunk_count": 2,
        "title": "Titre automatique",
        "category": "Juridique",
        "year": 2025,
        "person": "Amine",
        "department": "Direction",
        "document_type": "Contrat",
        "tags": ["contrat"],
    }
    assert repository.document == result


@pytest.mark.anyio
async def test_processing_error_sets_error_and_keeps_file(monkeypatch, tmp_path: Path):
    repository = FakeRepository()
    service, _, processor = make_service(
        repository,
        processor_error=RuntimeError("détail technique"),
    )
    monkeypatch.setattr("app.documents.service.DOCUMENTS_DIR", tmp_path)

    with pytest.raises(RuntimeError, match="détail technique"):
        await service.upload_document(make_upload())

    assert len(processor.calls) == 1
    assert repository.document is not None
    assert repository.document["status"] == "error"
    assert repository.document["error_message"] == (
        "Le traitement du document a échoué."
    )
    assert Path(repository.document["path"]).is_file()


@pytest.mark.anyio
async def test_initial_save_error_removes_file(monkeypatch, tmp_path: Path):
    repository = FakeRepository(save_error=RuntimeError("postgres indisponible"))
    service, _, processor = make_service(repository)
    monkeypatch.setattr("app.documents.service.DOCUMENTS_DIR", tmp_path)

    with pytest.raises(RuntimeError, match="postgres indisponible"):
        await service.upload_document(make_upload())

    assert list(tmp_path.iterdir()) == []
    assert processor.calls == []


@pytest.mark.parametrize("status", ["queued", "processing"])
def test_delete_rejects_active_documents(tmp_path: Path, status: str):
    repository = FakeRepository()
    service, vector_store, _ = make_service(repository)
    file_path = tmp_path / f"{status}.pdf"
    file_path.write_bytes(b"contenu")
    repository.document = {
        "id": "document-id",
        "status": status,
        "path": str(file_path),
    }

    with pytest.raises(DocumentDeletionConflictError):
        service.delete_document("document-id")

    assert file_path.is_file()
    assert repository.document is not None
    assert vector_store.deleted_ids == []


@pytest.mark.parametrize("status", ["ready", "error"])
def test_delete_allows_terminal_documents(tmp_path: Path, status: str):
    repository = FakeRepository()
    service, vector_store, _ = make_service(repository)
    file_path = tmp_path / f"{status}.pdf"
    file_path.write_bytes(b"contenu")
    repository.document = {
        "id": "document-id",
        "status": status,
        "path": str(file_path),
    }

    assert service.delete_document("document-id") is True
    assert not file_path.exists()
    assert repository.document is None
    assert vector_store.deleted_ids == ["document-id"]
