import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from app.documents.dispatcher import DocumentProcessingDispatcher
from app.documents.paths import resolve_document_path
from app.documents.repository import DocumentRepository


BACKEND_DIR = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = BACKEND_DIR / "documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)

DISPATCH_ERROR_MESSAGE = "Le traitement du document n'a pas pu être planifié."


class DocumentDeletionConflictError(Exception):
    """Le statut courant du document interdit sa suppression."""


class DocumentProcessingDispatchError(Exception):
    """Le traitement du document n'a pas pu être planifié."""


class DocumentService:
    """Service responsable du cycle de vie d'un document."""

    def __init__(
        self,
        repository: DocumentRepository,
        vector_store,
        dispatcher: DocumentProcessingDispatcher,
    ) -> None:
        self._repository = repository
        self._vector_store = vector_store
        self._dispatcher = dispatcher

    async def upload_document(
        self,
        file: UploadFile,
        *,
        title: str | None = None,
        category: str | None = None,
        year: int | None = None,
        person: str | None = None,
        department: str | None = None,
        document_type: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        if not file.filename:
            raise ValueError("Le fichier doit avoir un nom.")

        manual_metadata = self._build_business_metadata(
            title=title,
            category=category,
            year=year,
            person=person,
            department=department,
            document_type=document_type,
            tags=tags,
        )

        document_id = str(uuid4())
        original_name = file.filename
        extension = Path(original_name).suffix.lower()
        stored_filename = f"{document_id}{extension}"
        file_path = DOCUMENTS_DIR / stored_filename

        content = await file.read()
        if not content:
            raise ValueError("Le fichier est vide.")

        await run_in_threadpool(file_path.write_bytes, content)

        initial_metadata = {
            "id": document_id,
            "filename": original_name,
            "type": extension.lstrip("."),
            "size": len(content),
            "path": str(file_path),
            "created_at": datetime.now(timezone.utc),
            "status": "queued",
            "error_message": None,
            "page_count": None,
            "chunk_count": None,
            **manual_metadata,
            "tags": manual_metadata["tags"] if tags is not None else None,
        }

        try:
            await run_in_threadpool(self._repository.save, initial_metadata)
        except Exception:
            if file_path.exists():
                await run_in_threadpool(file_path.unlink)
            raise

        try:
            await run_in_threadpool(self._dispatcher.enqueue, document_id)
        except Exception as enqueue_error:
            logger.exception(
                "Échec de la planification du document %s.",
                document_id,
            )
            try:
                error_updated = await run_in_threadpool(
                    self._repository.update,
                    document_id,
                    {
                        "status": "error",
                        "error_message": DISPATCH_ERROR_MESSAGE,
                    },
                )
                if not error_updated:
                    raise RuntimeError(
                        "Le document en erreur est introuvable."
                    )
            except Exception:
                logger.exception(
                    "Impossible d'enregistrer l'échec de planification "
                    "du document %s.",
                    document_id,
                )

            raise DocumentProcessingDispatchError(
                DISPATCH_ERROR_MESSAGE
            ) from enqueue_error

        return {
            **initial_metadata,
            "tags": manual_metadata["tags"],
        }

    @staticmethod
    def _build_business_metadata(
        *,
        title: str | None,
        category: str | None,
        year: int | None,
        person: str | None,
        department: str | None,
        document_type: str | None,
        tags: list[str] | None,
    ) -> dict:
        """Normalise les métadonnées métier renseignées à l'import."""

        if year is not None and not 1000 <= year <= 9999:
            raise ValueError(
                "L'année doit être comprise entre 1000 et 9999."
            )

        def clean(value: str | None) -> str | None:
            if value is None:
                return None
            normalized = value.strip()
            return normalized or None

        normalized_tags: list[str] = []
        for tag in tags or []:
            normalized_tag = clean(tag)
            if normalized_tag and normalized_tag not in normalized_tags:
                normalized_tags.append(normalized_tag)

        return {
            "title": clean(title),
            "category": clean(category),
            "year": year,
            "person": clean(person),
            "department": clean(department),
            "document_type": clean(document_type),
            "tags": normalized_tags,
        }

    def get_documents(self) -> list[dict]:
        """Retourne la liste des documents enregistrés."""

        return self._repository.get_all()

    def get_document(self, document_id: str) -> dict | None:
        """Retourne les métadonnées d'un document."""

        return self._repository.get_by_id(document_id)

    def get_document_file(
        self,
        document_id: str,
    ) -> tuple[Path, dict] | None:
        """Retourne le fichier physique et ses métadonnées pour le viewer."""

        metadata = self.get_document(document_id)
        if metadata is None:
            return None

        file_path = resolve_document_path(metadata["path"])
        if not file_path.is_file():
            raise FileNotFoundError(
                "Le fichier du document n'est plus disponible."
            )

        return file_path, metadata

    def delete_document(self, document_id: str) -> bool:
        """Supprime un document de tous les stockages."""

        metadata = self._repository.get_by_id(document_id)
        if metadata is None:
            return False

        if metadata["status"] not in {"ready", "error"}:
            raise DocumentDeletionConflictError(
                "Un document en attente ou en cours de traitement "
                "ne peut pas être supprimé."
            )

        self._vector_store.delete_document(document_id)

        file_path = resolve_document_path(metadata["path"])
        if file_path.exists():
            file_path.unlink()

        self._repository.delete(document_id)
        return True
