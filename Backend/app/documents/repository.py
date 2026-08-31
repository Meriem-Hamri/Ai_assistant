from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.database.models.document import DocumentModel
from app.database.session import SessionLocal
from app.documents.processing_input import DocumentProcessingInput


class DocumentRepository:
    """Persiste les métadonnées des documents dans PostgreSQL."""

    _UPDATABLE_FIELDS = {
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
    }

    def save(self, metadata: dict) -> None:
        """Enregistre les métadonnées d'un document."""
        document = DocumentModel(
            id=UUID(metadata["id"]),
            filename=metadata["filename"],
            type=metadata["type"],
            size=metadata["size"],
            path=self._normalize_path(metadata["path"]),
            status=metadata["status"],
            error_message=metadata.get("error_message"),
            title=metadata.get("title"),
            category=metadata.get("category"),
            year=metadata.get("year"),
            person=metadata.get("person"),
            department=metadata.get("department"),
            document_type=metadata.get("document_type"),
            tags=metadata.get("tags"),
            page_count=metadata.get("page_count"),
            chunk_count=metadata.get("chunk_count"),
        )

        if metadata.get("created_at") is not None:
            document.created_at = metadata["created_at"]
        if metadata.get("updated_at") is not None:
            document.updated_at = metadata["updated_at"]

        with SessionLocal() as session:
            try:
                session.add(document)
                session.commit()
            except Exception:
                session.rollback()
                raise

    def get_all(self) -> list[dict]:
        """Retourne les documents, du plus récent au plus ancien."""
        with SessionLocal() as session:
            documents = session.scalars(
                select(DocumentModel).order_by(
                    DocumentModel.created_at.desc()
                )
            ).all()
            return [self._to_dict(document) for document in documents]

    def get_by_id(self, document_id: str) -> dict | None:
        """Retourne un document à partir de son identifiant."""
        parsed_id = self._parse_id(document_id)
        if parsed_id is None:
            return None

        with SessionLocal() as session:
            document = session.get(DocumentModel, parsed_id)
            if document is None:
                return None
            return self._to_dict(document)

    def get_for_processing(
        self,
        document_id: str,
    ) -> DocumentProcessingInput | None:
        """Retourne le contrat interne en préservant la valeur SQL de tags."""
        parsed_id = self._parse_id(document_id)
        if parsed_id is None:
            return None

        with SessionLocal() as session:
            document = session.get(DocumentModel, parsed_id)
            if document is None:
                return None
            return DocumentProcessingInput(
                id=str(document.id),
                filename=document.filename,
                path=document.path,
                status=document.status,
                title=document.title,
                category=document.category,
                year=document.year,
                person=document.person,
                department=document.department,
                document_type=document.document_type,
                tags=document.tags,
            )

    def update(self, document_id: str, updates: dict) -> bool:
        """Met à jour uniquement les champs modifiables d'un document."""
        parsed_id = self._parse_id(document_id)
        if parsed_id is None:
            return False

        with SessionLocal() as session:
            try:
                document = session.get(DocumentModel, parsed_id)
                if document is None:
                    return False

                for field, value in updates.items():
                    if field in self._UPDATABLE_FIELDS:
                        setattr(document, field, value)

                session.commit()
                return True
            except Exception:
                session.rollback()
                raise

    def delete(self, document_id: str) -> bool:
        """Supprime une ligne de métadonnées si elle existe."""
        parsed_id = self._parse_id(document_id)
        if parsed_id is None:
            return False

        with SessionLocal() as session:
            try:
                document = session.get(DocumentModel, parsed_id)
                if document is None:
                    return False

                session.delete(document)
                session.commit()
                return True
            except Exception:
                session.rollback()
                raise

    @staticmethod
    def _parse_id(document_id: str) -> UUID | None:
        try:
            return UUID(document_id)
        except (AttributeError, TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_path(stored_path: str) -> str:
        return (Path("documents") / Path(stored_path).name).as_posix()

    @staticmethod
    def _to_dict(document: DocumentModel) -> dict:
        return {
            "id": str(document.id),
            "filename": document.filename,
            "type": document.type,
            "size": document.size,
            "path": document.path,
            "status": document.status,
            "error_message": document.error_message,
            "title": document.title,
            "category": document.category,
            "year": document.year,
            "person": document.person,
            "department": document.department,
            "document_type": document.document_type,
            "tags": document.tags or [],
            "page_count": document.page_count,
            "chunk_count": document.chunk_count,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }
