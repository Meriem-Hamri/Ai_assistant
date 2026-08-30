from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.cleaning.cleaner import clean_document
from app.documents.indexer import DocumentIndexer
from app.documents.repository import DocumentRepository
from app.extraction.extraction_service import extract_document
from app.metadata.extractor import MetadataExtractor


DOCUMENTS_DIR = Path("documents")
DOCUMENTS_DIR.mkdir(exist_ok=True)


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

        file_path.write_bytes(content)

        try:
            document = extract_document(
                str(file_path)
            )

            for page in document.pages:
                page.text = clean_document(
                    page.text
                )

            automatic_metadata = self._metadata_extractor.extract(
                "\n\n".join(page.text for page in document.pages)
            ).to_dict()
            business_metadata = self._merge_business_metadata(
                automatic_metadata=automatic_metadata,
                manual_metadata=manual_metadata,
                manual_tags_provided=tags is not None,
            )

            document.id = document_id
            document.filename = original_name
            document.metadata.update(business_metadata)

            chunks = self._indexer.index(
                document
            )

            metadata = {
                "id": document_id,
                "filename": original_name,
                "type": extension.lstrip("."),
                "page_count": len(document.pages),
                "size": len(content),
                "created_at": datetime.now(
                    timezone.utc
                ),
                "status": "ready",
                "path": str(file_path),
                "chunk_count": len(chunks),
                **business_metadata,
            }

            self._repository.save(
                metadata
            )

            return metadata

        except Exception:

            if file_path.exists():
                file_path.unlink()

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
        Retourne la liste des documents enregistrés.
        """

        return self._repository.get_all()

    def get_document(
        self,
        document_id: str,
    ) -> dict | None:
        """
        Retourne les métadonnées d'un document.
        """

        return self._repository.get_by_id(
            document_id
        )

    def get_document_file(
        self,
        document_id: str,
    ) -> tuple[Path, dict] | None:
        """Retourne le fichier physique et ses métadonnées pour le viewer."""

        metadata = self.get_document(document_id)
        if metadata is None:
            return None

        file_path = Path(metadata["path"])
        if not file_path.is_file():
            raise FileNotFoundError(
                "Le fichier du document n'est plus disponible."
            )

        return file_path, metadata

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

        self._vector_store.delete_document(
            document_id
        )

        file_path = Path(
            metadata["path"]
        )

        if file_path.exists():
            file_path.unlink()

        self._repository.delete(
            document_id
        )

        return True
