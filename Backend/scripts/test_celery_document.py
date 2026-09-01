from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.documents.repository import DocumentRepository
from app.tasks.documents import process_document


def main() -> None:
    source = Path("documents/docx/test_rag.docx")

    if not source.is_file():
        raise FileNotFoundError(
            f"Fichier de test introuvable : {source}"
        )

    document_id = str(uuid4())
    extension = source.suffix.lower()

    destination = Path("documents") / f"{document_id}{extension}"

    destination.write_bytes(source.read_bytes())

    metadata = {
        "id": document_id,
        "filename": source.name,
        "type": extension.lstrip("."),
        "size": destination.stat().st_size,
        "path": str(destination),
        "created_at": datetime.now(timezone.utc),
        "status": "queued",
        "error_message": None,
        "page_count": None,
        "chunk_count": None,
        "title": None,
        "category": None,
        "year": None,
        "person": None,
        "department": None,
        "document_type": None,
        "tags": None,
    }

    repository = DocumentRepository()
    repository.save(metadata)

    print(f"Document créé : {document_id}")
    print(f"Fichier copié : {destination}")
    print("Statut initial : queued")

    result = process_document.delay(document_id)

    print(f"Tâche Celery envoyée : {result.id}")
    print("Le worker doit maintenant traiter le document.")


if __name__ == "__main__":
    main()