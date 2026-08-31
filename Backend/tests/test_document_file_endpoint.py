import os
from pathlib import Path

from fastapi.testclient import TestClient

# Les tests d'API utilisent le modèle BGE-M3 déjà disponible localement.
os.environ["HF_HUB_OFFLINE"] = "1"

from app.api.main import app
from app.api.routes.documents import get_document_service
from app.documents.service import DocumentService


class FakeRepository:
    def __init__(self, documents: dict[str, dict]) -> None:
        self.documents = documents

    def get_by_id(self, document_id: str) -> dict | None:
        return self.documents.get(document_id)


def create_service(documents: dict[str, dict]) -> DocumentService:
    return DocumentService(
        indexer=None,
        repository=FakeRepository(documents),
        vector_store=None,
        metadata_extractor=object(),
    )


def test_serves_pdf_inline(tmp_path: Path):
    file_path = tmp_path / "contrat.pdf"
    file_path.write_bytes(b"%PDF-1.4 test")
    service = create_service(
        {
            "pdf-1": {
                "id": "pdf-1",
                "filename": "contrat.pdf",
                "type": "pdf",
                "path": str(file_path),
            }
        }
    )
    app.dependency_overrides[get_document_service] = lambda: service

    try:
        response = TestClient(app).get("/documents/pdf-1/file")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 test"
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == 'inline; filename="contrat.pdf"'


def test_serves_docx_as_download_when_requested(tmp_path: Path):
    file_path = tmp_path / "rapport.docx"
    file_path.write_bytes(b"DOCX test")
    service = create_service(
        {
            "docx-1": {
                "id": "docx-1",
                "filename": "rapport.docx",
                "type": "docx",
                "path": str(file_path),
            }
        }
    )
    app.dependency_overrides[get_document_service] = lambda: service

    try:
        response = TestClient(app).get(
            "/documents/docx-1/file?download=true"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    )
    assert response.headers["content-disposition"] == (
        'attachment; filename="rapport.docx"'
    )


def test_returns_404_for_unknown_document():
    app.dependency_overrides[get_document_service] = lambda: create_service({})

    try:
        response = TestClient(app).get("/documents/inconnu/file")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Document introuvable."
