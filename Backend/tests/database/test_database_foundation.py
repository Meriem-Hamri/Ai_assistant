import uuid

from sqlalchemy import inspect, select

from app.database.models import DocumentModel
from app.database.session import SessionLocal, engine


def test_documents_table_has_expected_columns():
    inspector = inspect(engine)

    columns = inspector.get_columns("documents")
    column_names = {column["name"] for column in columns}

    expected_columns = {
        "id",
        "filename",
        "type",
        "size",
        "path",
        "status",
        "error_message",
        "title",
        "category",
        "year",
        "person",
        "department",
        "document_type",
        "tags",
        "page_count",
        "chunk_count",
        "created_at",
        "updated_at",
    }

    assert expected_columns == column_names


def test_document_can_be_inserted_and_read():
    session = SessionLocal()

    path = f"documents/db-test-{uuid.uuid4()}.pdf"
    document = DocumentModel(
        filename="database-test.pdf",
        type="pdf",
        size=1234,
        path=path,
        status="queued",
    )

    try:
        session.add(document)
        session.commit()
        session.refresh(document)

        result = session.execute(
            select(DocumentModel).where(
                DocumentModel.id == document.id
            )
        ).scalar_one()

        assert result.filename == "database-test.pdf"
        assert result.type == "pdf"
        assert result.size == 1234
        assert result.path == path
        assert result.status == "queued"
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None

    finally:
        session.rollback()

        persisted_document = session.execute(
            select(DocumentModel).where(
                DocumentModel.path == path
            )
        ).scalar_one_or_none()

        if persisted_document is not None:
            session.delete(persisted_document)
            session.commit()

        session.close()
