from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import null, select, update

from app.database.models import DocumentModel
from app.database.session import SessionLocal
from app.api.schemas.document import DocumentResponse
from app.documents.processing_input import DocumentProcessingInput
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
        "ocr_language": "ar",
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
            assert document.ocr_language == metadata["ocr_language"]
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
            "chunk_count", "ocr_language", "created_at", "updated_at",
        }
        assert result["filename"] == metadata["filename"]
        assert result["type"] == metadata["type"]
        assert result["size"] == metadata["size"]
        assert result["path"] == metadata["path"]
        assert result["status"] == metadata["status"]
        assert result["page_count"] == metadata["page_count"]
        assert result["chunk_count"] == metadata["chunk_count"]
        assert result["ocr_language"] == metadata["ocr_language"]
        assert result["created_at"] == metadata["created_at"]
        assert result["updated_at"] is not None
        response = DocumentResponse.model_validate(result)
        assert response.id == metadata["id"]
        assert repository.get_by_id(str(uuid4())) is None
        assert repository.get_by_id("abc") is None
    finally:
        cleanup_documents(metadata["id"])


def test_get_by_ids_empty_returns_without_opening_a_session(monkeypatch):
    repository = DocumentRepository()

    def fail_if_called():
        raise AssertionError(
            "Une sélection vide ne doit pas interroger PostgreSQL"
        )

    monkeypatch.setattr("app.documents.repository.SessionLocal", fail_if_called)

    assert repository.get_by_ids([]) == []


def test_get_by_ids_returns_multiple_documents_in_requested_order():
    repository = DocumentRepository()
    first = build_metadata()
    second = build_metadata(status="processing")

    try:
        repository.save(first)
        repository.save(second)

        results = repository.get_by_ids([second["id"], first["id"]])

        assert [result["id"] for result in results] == [
            second["id"],
            first["id"],
        ]
        assert [result["status"] for result in results] == [
            "processing",
            "ready",
        ]
    finally:
        cleanup_documents(first["id"], second["id"])


def test_get_by_ids_ignores_invalid_uuid_for_business_level_validation():
    repository = DocumentRepository()
    metadata = build_metadata()

    try:
        repository.save(metadata)

        assert repository.get_by_ids(["uuid-invalide", metadata["id"]]) == [
            repository.get_by_id(metadata["id"])
        ]
        assert repository.get_by_ids(["uuid-invalide"]) == []
    finally:
        cleanup_documents(metadata["id"])


@pytest.mark.parametrize(
    ("persisted_tags", "expected_processing_tags"),
    [
        (None, None),
        ([], []),
        (["audit"], ["audit"]),
    ],
)
def test_get_for_processing_preserves_tags_intent(
    persisted_tags,
    expected_processing_tags,
):
    repository = DocumentRepository()
    metadata = build_metadata(tags=persisted_tags)

    try:
        repository.save(metadata)
        if persisted_tags is None:
            with SessionLocal() as session:
                session.execute(
                    update(DocumentModel)
                    .where(DocumentModel.id == UUID(metadata["id"]))
                    .values(tags=null())
                )
                session.commit()

        public_document = repository.get_by_id(metadata["id"])
        processing_input = repository.get_for_processing(metadata["id"])

        assert public_document is not None
        assert public_document["tags"] == (persisted_tags or [])
        assert isinstance(processing_input, DocumentProcessingInput)
        assert processing_input.id == metadata["id"]
        assert processing_input.filename == metadata["filename"]
        assert processing_input.path == metadata["path"]
        assert processing_input.status == metadata["status"]
        assert processing_input.title == metadata["title"]
        assert processing_input.category == metadata["category"]
        assert processing_input.year == metadata["year"]
        assert processing_input.person == metadata["person"]
        assert processing_input.department == metadata["department"]
        assert processing_input.document_type == metadata["document_type"]
        assert processing_input.tags == expected_processing_tags
        assert processing_input.ocr_language == metadata["ocr_language"]
    finally:
        cleanup_documents(metadata["id"])


def test_get_for_processing_handles_invalid_and_unknown_ids():
    repository = DocumentRepository()

    assert repository.get_for_processing("abc") is None
    assert repository.get_for_processing(str(uuid4())) is None


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


def test_update_applies_lifecycle_and_business_fields():
    repository = DocumentRepository()
    old_updated_at = datetime.now(timezone.utc) - timedelta(days=1)
    metadata = build_metadata(
        status="queued",
        error_message=None,
        title=None,
        category=None,
        year=None,
        person=None,
        department=None,
        document_type=None,
        tags=None,
        page_count=None,
        chunk_count=None,
        updated_at=old_updated_at,
    )
    updates = {
        "status": "ready",
        "error_message": None,
        "title": "Rapport annuel",
        "category": "Finance",
        "year": 2026,
        "person": "Nadia",
        "department": "Comptabilité",
        "document_type": "Rapport",
        "tags": ["annuel", "finance"],
        "page_count": 12,
        "chunk_count": 24,
    }

    try:
        repository.save(metadata)

        assert repository.update(metadata["id"], updates) is True

        result = repository.get_by_id(metadata["id"])
        assert result is not None
        for field, value in updates.items():
            assert result[field] == value
        assert result["updated_at"] > old_updated_at
    finally:
        cleanup_documents(metadata["id"])


def test_update_rejects_invalid_and_unknown_ids():
    repository = DocumentRepository()

    assert repository.update("abc", {"status": "ready"}) is False
    assert repository.update(str(uuid4()), {"status": "ready"}) is False


def test_update_ignores_forbidden_fields():
    repository = DocumentRepository()
    metadata = build_metadata(status="queued")
    forbidden_updates = {
        "id": str(uuid4()),
        "filename": "modifie.pdf",
        "type": "docx",
        "size": 1,
        "path": "documents/modifie.pdf",
        "created_at": datetime.now(timezone.utc) - timedelta(days=30),
    }

    try:
        repository.save(metadata)

        assert repository.update(metadata["id"], forbidden_updates) is True

        result = repository.get_by_id(metadata["id"])
        assert result is not None
        for field in forbidden_updates:
            assert result[field] == metadata[field]
    finally:
        cleanup_documents(metadata["id"])
