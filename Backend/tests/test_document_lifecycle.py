from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes.documents import get_document_service
from app.api.schemas.document import DocumentResponse
from app.documents.service import (
    DISPATCH_ERROR_MESSAGE,
    DocumentDeletionConflictError,
    DocumentProcessingDispatchError,
    DocumentService,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


class FakeRepository:
    def __init__(
        self,
        *,
        save_error: Exception | None = None,
        update_error: Exception | None = None,
    ) -> None:
        self.document: dict | None = None
        self.events: list[tuple[str, str]] = []
        self.save_error = save_error
        self.update_error = update_error

    def save(self, metadata: dict) -> None:
        self.events.append(("save", metadata["status"]))
        if self.save_error is not None:
            raise self.save_error
        self.document = dict(metadata)

    def update(self, document_id: str, updates: dict) -> bool:
        self.events.append(("update", updates["status"]))
        if self.update_error is not None:
            raise self.update_error
        if self.document is None or self.document["id"] != document_id:
            return False
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


class FakeDispatcher:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.document_ids: list[str] = []

    def enqueue(self, document_id: str) -> None:
        self.document_ids.append(document_id)
        if self.error is not None:
            raise self.error


class FakeVectorStore:
    def __init__(self) -> None:
        self.deleted_ids: list[str] = []

    def delete_document(self, document_id: str) -> None:
        self.deleted_ids.append(document_id)


def make_service(
    repository: FakeRepository,
    *,
    dispatcher_error: Exception | None = None,
) -> tuple[DocumentService, FakeVectorStore, FakeDispatcher]:
    vector_store = FakeVectorStore()
    dispatcher = FakeDispatcher(error=dispatcher_error)
    return (
        DocumentService(
            repository=repository,
            vector_store=vector_store,
            dispatcher=dispatcher,
        ),
        vector_store,
        dispatcher,
    )


def make_upload(content: bytes = b"contenu") -> UploadFile:
    return UploadFile(filename="rapport.pdf", file=BytesIO(content))


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
            "error_message": "erreur" if status == "error" else None,
            "chunk_count": None,
        }
    )

    assert response.status == status
    assert response.page_count is None


@pytest.mark.anyio
async def test_upload_saves_queued_document_and_enqueues_only_its_id(
    monkeypatch,
    tmp_path: Path,
):
    repository = FakeRepository()
    service, _, dispatcher = make_service(repository)
    monkeypatch.setattr("app.documents.service.DOCUMENTS_DIR", tmp_path)

    result = await service.upload_document(make_upload())
    response = DocumentResponse.model_validate(result)

    assert repository.events == [("save", "queued")]
    assert repository.document is not None
    assert repository.document["id"] == result["id"]
    assert repository.document["status"] == result["status"]
    assert dispatcher.document_ids == [result["id"]]
    assert result["status"] == "queued"
    assert result["page_count"] is None
    assert result["chunk_count"] is None
    assert result["ocr_language"] == "fr"
    assert response.status == "queued"
    assert response.tags == []
    assert Path(result["path"]).read_bytes() == b"contenu"


@pytest.mark.anyio
async def test_upload_accepts_explicit_ocr_language(monkeypatch, tmp_path: Path):
    repository = FakeRepository()
    service, _, _ = make_service(repository)
    monkeypatch.setattr("app.documents.service.DOCUMENTS_DIR", tmp_path)

    result = await service.upload_document(make_upload(), ocr_language="mixed")

    assert result["ocr_language"] == "mixed"
    assert repository.document["ocr_language"] == "mixed"


def test_upload_route_rejects_invalid_ocr_language_with_422():
    response = TestClient(app).post(
        "/documents/",
        files={"file": ("rapport.pdf", b"contenu", "application/pdf")},
        data={"ocr_language": "auto"},
    )

    assert response.status_code == 422


def test_upload_route_accepts_ocr_language():
    class CapturingService:
        def __init__(self):
            self.ocr_language = None

        async def upload_document(self, file, **kwargs):
            self.ocr_language = kwargs["ocr_language"]
            return {
                "id": "document-id",
                "filename": file.filename,
                "type": "pdf",
                "size": 7,
                "created_at": "2026-09-01T12:00:00Z",
                "status": "queued",
                "ocr_language": self.ocr_language,
            }

    service = CapturingService()
    app.dependency_overrides[get_document_service] = lambda: service
    try:
        response = TestClient(app).post(
            "/documents/",
            files={"file": ("rapport.pdf", b"contenu", "application/pdf")},
            data={"ocr_language": "ar"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["ocr_language"] == "ar"
    assert service.ocr_language == "ar"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("tags", "expected"),
    [(None, None), ([], []), (["audit"], ["audit"])],
)
async def test_upload_preserves_manual_tags_contract(
    monkeypatch,
    tmp_path: Path,
    tags,
    expected,
):
    repository = FakeRepository()
    service, _, dispatcher = make_service(repository)
    monkeypatch.setattr("app.documents.service.DOCUMENTS_DIR", tmp_path)

    result = await service.upload_document(make_upload(), tags=tags)

    assert repository.document is not None
    assert repository.document["tags"] == expected
    assert result["tags"] == (expected or [])
    assert dispatcher.document_ids == [result["id"]]


@pytest.mark.anyio
async def test_initial_save_error_removes_file_and_does_not_enqueue(
    monkeypatch,
    tmp_path: Path,
):
    repository = FakeRepository(save_error=RuntimeError("postgres indisponible"))
    service, _, dispatcher = make_service(repository)
    monkeypatch.setattr("app.documents.service.DOCUMENTS_DIR", tmp_path)

    with pytest.raises(RuntimeError, match="postgres indisponible"):
        await service.upload_document(make_upload())

    assert list(tmp_path.iterdir()) == []
    assert dispatcher.document_ids == []


@pytest.mark.anyio
async def test_empty_file_is_rejected_before_save_or_enqueue(
    monkeypatch,
    tmp_path: Path,
):
    repository = FakeRepository()
    service, _, dispatcher = make_service(repository)
    monkeypatch.setattr("app.documents.service.DOCUMENTS_DIR", tmp_path)

    with pytest.raises(ValueError, match="vide"):
        await service.upload_document(make_upload(b""))

    assert repository.events == []
    assert dispatcher.document_ids == []
    assert list(tmp_path.iterdir()) == []


@pytest.mark.anyio
async def test_enqueue_error_marks_document_error_and_keeps_file(
    monkeypatch,
    tmp_path: Path,
):
    enqueue_error = RuntimeError("redis://secret-host:6379 indisponible")
    repository = FakeRepository()
    service, _, dispatcher = make_service(
        repository,
        dispatcher_error=enqueue_error,
    )
    monkeypatch.setattr("app.documents.service.DOCUMENTS_DIR", tmp_path)

    with pytest.raises(DocumentProcessingDispatchError) as raised:
        await service.upload_document(make_upload())

    assert raised.value.__cause__ is enqueue_error
    assert len(dispatcher.document_ids) == 1
    assert repository.events == [("save", "queued"), ("update", "error")]
    assert repository.document is not None
    assert repository.document["status"] == "error"
    assert repository.document["error_message"] == DISPATCH_ERROR_MESSAGE
    assert Path(repository.document["path"]).is_file()


@pytest.mark.anyio
async def test_update_error_does_not_replace_enqueue_error_cause(
    monkeypatch,
    tmp_path: Path,
):
    enqueue_error = RuntimeError("redis indisponible")
    repository = FakeRepository(update_error=RuntimeError("postgres indisponible"))
    service, _, _ = make_service(repository, dispatcher_error=enqueue_error)
    monkeypatch.setattr("app.documents.service.DOCUMENTS_DIR", tmp_path)

    with pytest.raises(DocumentProcessingDispatchError) as raised:
        await service.upload_document(make_upload())

    assert raised.value.__cause__ is enqueue_error
    assert repository.document is not None
    assert repository.document["status"] == "queued"
    assert Path(repository.document["path"]).is_file()


def test_upload_route_maps_dispatch_error_to_503():
    class FailingService:
        async def upload_document(self, *args, **kwargs):
            raise DocumentProcessingDispatchError(DISPATCH_ERROR_MESSAGE)

    app.dependency_overrides[get_document_service] = lambda: FailingService()
    try:
        response = TestClient(app).post(
            "/documents/",
            files={"file": ("rapport.pdf", b"contenu", "application/pdf")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": DISPATCH_ERROR_MESSAGE}


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
