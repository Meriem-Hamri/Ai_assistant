from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.cleaning.cleaner import clean_document
from app.documents.indexer import DocumentIndexer
from app.documents.repository import DocumentRepository
from app.extraction.extraction_service import extract_document


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
    ) -> None:
        self._indexer = indexer
        self._repository = repository

    async def upload_document(
        self,
        file: UploadFile,
    ) -> dict:

        if not file.filename:
            raise ValueError(
                "Le fichier doit avoir un nom."
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

            document.id = document_id

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
            }

            self._repository.save(
                metadata
            )

            return metadata

        except Exception:

            if file_path.exists():
                file_path.unlink()

            raise

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