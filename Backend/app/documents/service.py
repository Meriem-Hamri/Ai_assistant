import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.cleaning.cleaner import clean_document
from app.documents.indexer import DocumentIndexer
from app.documents.repository import DocumentRepository
from app.extraction.extraction_service import extract_document
from app.metadata.extractor import MetadataExtractor
from starlette.concurrency import run_in_threadpool

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
DOCUMENTS_DIR = BACKEND_DIR / "documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)


class DocumentDeletionConflictError(Exception):
    """Le statut courant du document interdit sa suppression."""


class DocumentService:
    """
    Service responsable du cycle de vie d'un document.
    """

    def __init__(
        self,
        indexer: DocumentIndexer,
        repository: DocumentRepository,
        vector_store,
        metadata_extractor: MetadataExtractor | None = None,
    ) -> None:
        self._indexer = indexer
        self._repository = repository
        self._vector_store = vector_store
        self._metadata_extractor = metadata_extractor or MetadataExtractor()

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
            raise ValueError(
                "Le fichier doit avoir un nom."
            )

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

        extension = Path(
            original_name
        ).suffix.lower()

        stored_filename = (
            f"{document_id}{extension}"
        )

        file_path = (
            DOCUMENTS_DIR / stored_filename
        )

        content = await file.read()

        if not content:
            raise ValueError(
                "Le fichier est vide."
            )

        await run_in_threadpool(
            file_path.write_bytes,
            content,
        )

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
            await run_in_threadpool(
                self._repository.save,
                initial_metadata,
            )
        except Exception:
            if file_path.exists():
                await run_in_threadpool(file_path.unlink)
            raise

        try:
            processing_updated = await run_in_threadpool(
                self._repository.update,
                document_id,
                {"status": "processing", "error_message": None},
            )
            if not processing_updated:
                raise RuntimeError(
                    "Le document enregistré est introuvable."
                )

            processing_result = await run_in_threadpool(
                self._process_document,
                file_path,
                document_id,
                original_name,
                manual_metadata,
                tags is not None,
            )

            ready_updates = {
                "status": "ready",
                "error_message": None,
                **processing_result,
            }
            ready_updated = await run_in_threadpool(
                self._repository.update,
                document_id,
                ready_updates,
            )
            if not ready_updated:
                raise RuntimeError(
                    "Le document traité est introuvable."
                )

            return {**initial_metadata, **ready_updates}

        except Exception:
            logger.exception(
                "Échec du traitement du document %s.",
                document_id,
            )
            try:
                await run_in_threadpool(
                    self._repository.update,
                    document_id,
                    {
                        "status": "error",
                        "error_message": (
                            "Le traitement du document a échoué."
                        ),
                    },
                )
            except Exception:
                logger.exception(
                    "Impossible d'enregistrer l'échec du document %s.",
                    document_id,
                )

            raise

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
        """Normalise les mÃ©tadonnÃ©es mÃ©tier renseignÃ©es Ã  l'import."""

        if year is not None and not 1000 <= year <= 9999:
            raise ValueError(
                "L'annÃ©e doit Ãªtre comprise entre 1000 et 9999."
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

    @staticmethod
    def _merge_business_metadata(
        *,
        automatic_metadata: dict,
        manual_metadata: dict,
        manual_tags_provided: bool,
    ) -> dict:
        """Les corrections manuelles priment sur l'analyse automatique."""

        merged_metadata = dict(automatic_metadata)

        for key in (
            "title",
            "category",
            "year",
            "person",
            "department",
            "document_type",
        ):
            if manual_metadata[key] is not None:
                merged_metadata[key] = manual_metadata[key]

        if manual_tags_provided:
            merged_metadata["tags"] = manual_metadata["tags"]

        return merged_metadata

    def get_documents(self) -> list[dict]:
        """
        Retourne la liste des documents enregistrÃ©s.
        """

        return self._repository.get_all()

    def get_document(
        self,
        document_id: str,
    ) -> dict | None:
        """
        Retourne les mÃ©tadonnÃ©es d'un document.
        """

        return self._repository.get_by_id(
            document_id
        )

    def get_document_file(
        self,
        document_id: str,
    ) -> tuple[Path, dict] | None:
        """Retourne le fichier physique et ses mÃ©tadonnÃ©es pour le viewer."""

        metadata = self.get_document(document_id)
        if metadata is None:
            return None

        file_path = self._resolve_document_path(metadata["path"])
        if not file_path.is_file():
            raise FileNotFoundError(
                "Le fichier du document n'est plus disponible."
            )

        return file_path, metadata

    @staticmethod
    def _resolve_document_path(stored_path: str) -> Path:
        """Résout les fichiers backend et les chemins historiques du projet."""

        path = Path(stored_path)
        if path.is_absolute():
            return path

        backend_path = BACKEND_DIR / path
        if backend_path.exists():
            return backend_path

        return PROJECT_ROOT / path

    def delete_document(
        self,
        document_id: str,
    ) -> bool:
        """
        Supprime un document de tous les stockages.
        """

        metadata = self._repository.get_by_id(
            document_id
        )

        if metadata is None:
            return False

        if metadata["status"] not in {"ready", "error"}:
            raise DocumentDeletionConflictError(
                "Un document en attente ou en cours de traitement "
                "ne peut pas être supprimé."
            )

        self._vector_store.delete_document(
            document_id
        )

        file_path = self._resolve_document_path(metadata["path"])

        if file_path.exists():
            file_path.unlink()

        self._repository.delete(
            document_id
        )

        return True

    def _process_document(
        self,
        file_path: Path,
        document_id: str,
        original_name: str,
        manual_metadata: dict,
        manual_tags_provided: bool,
    ) -> dict:
        """
        Exécute le pipeline synchrone et coûteux
        de traitement d'un document.

        Cette méthode doit être appelée depuis un threadpool
        afin de ne pas bloquer l'event loop FastAPI.
        """

        document = extract_document(
            str(file_path)
        )

        for page in document.pages:
            page.text = clean_document(
                page.text
            )

        document_text = "\n\n".join(
            page.text
            for page in document.pages
        )

        automatic_metadata = (
            self._metadata_extractor
            .extract(document_text)
            .to_dict()
        )

        business_metadata = (
            self._merge_business_metadata(
                automatic_metadata=automatic_metadata,
                manual_metadata=manual_metadata,
                manual_tags_provided=manual_tags_provided,
            )
        )

        document.id = document_id
        document.filename = original_name

        document.metadata.update(
            business_metadata
        )

        chunks = self._indexer.index(
            document
        )

        return {
            "page_count": len(document.pages),
            "chunk_count": len(chunks),
            **business_metadata,
        }
