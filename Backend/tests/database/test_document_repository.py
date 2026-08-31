from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select

from app.database.models import DocumentModel
from app.database.session import SessionLocal
from app.api.schemas.document import DocumentResponse
from app.documents.repository import DocumentRepository


def build_metadata(**overrides) -> dict:
    document_id = str(uuid4())
    metadata = {
        "id": document_id,
        "filename": f"repository-{document_id}.pdf",
        "type": "pdf",
        "page_count": 3,
        "size": 4096,
        "created_at": datetime.now(timezone.utc),
        "status": "ready",
        "path": f"documents/{document_id}.pdf",
        "chunk_count": 7,
        "title": "Contrat de travail",
        "category": "RH",
        "year": 2026,
        "person": "Ahmed",
        "department": "Ressources humaines",
        "document_type": "Contrat",
        "tags": ["contrat", "emploi"],
    }
    metadata.update(overrides)
    return metadata


def cleanup_documents(*document_ids: str) -> None:
    parsed_ids = [UUID(document_id) for document_id in document_ids]
    with SessionLocal() as session:
        documents = session.scalars(
            select(DocumentModel).where(DocumentModel.id.in_(parsed_ids))
        ).all()
        for document in documents:
            session.delete(document)
        session.commit()


def test_save_persists_document_and_business_metadata(tmp_path):
    repository = DocumentRepository()
    metadata = build_metadata()
    filename = f"{metadata['id']}.pdf"
    absolute_path = tmp_path / "Backend" / "documents" / filename
    metadata["path"] = str(absolute_path)

    try:
        repository.save(metadata)

        with SessionLocal() as session:
            document = session.get(DocumentModel, UUID(metadata["id"]))

            assert document is not None
            assert isinstance(document.id, UUID)
            assert document.filename == metadata["filename"]
            assert document.type == metadata["type"]
            assert document.size == metadata["size"]
            assert document.path == f"documents/{filename}"
            assert document.status == metadata["status"]
            assert document.title == metadata["title"]
            assert document.category == metadata["category"]
            assert document.year == metadata["year"]
            assert document.person == metadata["person"]
            assert document.department == metadata["department"]
            assert document.document_type == metadata["document_type"]
            assert document.tags == metadata["tags"]
    finally:
        cleanup_documents(metadata["id"])


def test_get_by_id_returns_contract_and_handles_unknown_ids():
    repository = DocumentRepository()
    metadata = build_metadata()

    try:
        repository.save(metadata)

        result = repository.get_by_id(metadata["id"])

        assert result is not None
        assert result["id"] == metadata["id"]
        assert set(result) == {
            "id", "filename", "type", "size", "path", "status",
            "error_message", "title", "category", "year", "person",
            "department", "document_type", "tags", "page_count",
            "chunk_count", "created_at", "updated_at",
        }
        assert result["filename"] == metadata["filename"]
        assert result["type"] == metadata["type"]
        assert result["size"] == metadata["size"]
        assert result["path"] == metadata["path"]
        assert result["status"] == metadata["status"]
        assert result["page_count"] == metadata["page_count"]
        assert result["chunk_count"] == metadata["chunk_count"]
        assert result["created_at"] == metadata["created_at"]
        assert result["updated_at"] is not None
        response = DocumentResponse.model_validate(result)
        assert response.id == metadata["id"]
        assert repository.get_by_id(str(uuid4())) is None
        assert repository.get_by_id("abc") is None
    finally:
        cleanup_documents(metadata["id"])


def test_get_all_returns_dicts_ordered_by_newest_first():
    repository = DocumentRepository()
    older = build_metadata(
        created_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    newer = build_metadata(created_at=datetime.now(timezone.utc))

    try:
        repository.save(older)
        repository.save(newer)

        documents = repository.get_all()
        positions = {
            document["id"]: position
            for position, document in enumerate(documents)
            if document["id"] in {older["id"], newer["id"]}
        }

        assert all(isinstance(document, dict) for document in documents)
        assert positions[newer["id"]] < positions[older["id"]]
    finally:
        cleanup_documents(older["id"], newer["id"])


def test_delete_removes_existing_document_and_handles_unknown_ids():
    repository = DocumentRepository()
    metadata = build_metadata()

    try:
        repository.save(metadata)

        assert repository.delete(metadata["id"]) is True
        assert repository.get_by_id(metadata["id"]) is None
        assert repository.delete(str(uuid4())) is False
        assert repository.delete("abc") is False
    finally:
        cleanup_documents(metadata["id"])
