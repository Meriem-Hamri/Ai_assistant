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
        "original_name",
        "stored_name",
        "extension",
        "file_size",
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

    stored_name = f"db-test-{uuid.uuid4()}.pdf"
    document = DocumentModel(
        original_name="database-test.pdf",
        stored_name=stored_name,
        extension=".pdf",
        file_size=1234,
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

        assert result.original_name == "database-test.pdf"
        assert result.stored_name == stored_name
        assert result.extension == ".pdf"
        assert result.file_size == 1234
        assert result.status == "queued"
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None

    finally:
        session.rollback()

        persisted_document = session.execute(
            select(DocumentModel).where(
                DocumentModel.stored_name == stored_name
            )
        ).scalar_one_or_none()

        if persisted_document is not None:
            session.delete(persisted_document)
            session.commit()

        session.close()