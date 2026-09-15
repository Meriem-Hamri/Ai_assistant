import logging

from app.celery_app import celery_app
from app.container import (
    create_document_processor,
    get_document_repository,
)
from app.documents.paths import resolve_document_path
from app.metadata.catalog import merge_reference_values


logger = logging.getLogger(__name__)

PROCESSING_ERROR_MESSAGE = "Le traitement du document a échoué."


@celery_app.task(name="app.tasks.documents.process_document")
def process_document(document_id: str) -> None:
    """Traite un document en attente à partir de son seul identifiant."""

    repository = get_document_repository()
    document = repository.get_for_processing(document_id)

    if document is None:
        logger.warning(
            "Document %s introuvable, traitement ignoré.",
            document_id,
        )
        return

    if document.status != "queued":
        logger.info(
            "Document %s au statut %s, traitement ignoré.",
            document_id,
            document.status,
        )
        return

    try:
        processing_updated = repository.update(
            document_id,
            {
                "status": "processing",
                "error_message": None,
            },
        )
        if not processing_updated:
            raise RuntimeError(
                "Le document a disparu avant le début du traitement."
            )

        file_path = resolve_document_path(document.path)
        if not file_path.is_file():
            raise FileNotFoundError(
                f"Le fichier du document {document_id} est introuvable."
            )

        manual_metadata = {
            "title": document.title,
            "category": document.category,
            "year": document.year,
            "person": document.person,
            "department": document.department,
            "document_type": document.document_type,
            "tags": document.tags or [],
        }
        manual_tags_provided = document.tags is not None

        processor = create_document_processor()
        get_values = getattr(repository, "get_distinct_metadata_values", None)
        existing_values = get_values() if get_values is not None else {}
        reference_values = {
            field: merge_reference_values(field, existing_values.get(field, []))
            for field in ("category", "department", "document_type")
        }
        result = processor.process(
            file_path=file_path,
            document_id=document.id,
            filename=document.filename,
            manual_metadata=manual_metadata,
            manual_tags_provided=manual_tags_provided,
            reference_values=reference_values,
            ocr_language=document.ocr_language,
        )

        ready_updated = repository.update(
            document_id,
            {
                "status": "ready",
                "error_message": None,
                "page_count": result.page_count,
                "chunk_count": result.chunk_count,
                "title": result.title,
                "category": result.category,
                "year": result.year,
                "person": result.person,
                "department": result.department,
                "document_type": result.document_type,
                "tags": result.tags,
            },
        )
        if not ready_updated:
            raise RuntimeError(
                "Le document a disparu après son traitement."
            )
    except Exception:
        logger.exception(
            "Échec du traitement du document %s.",
            document_id,
        )
        try:
            error_updated = repository.update(
                document_id,
                {
                    "status": "error",
                    "error_message": PROCESSING_ERROR_MESSAGE,
                },
            )
            if not error_updated:
                raise RuntimeError(
                    "Le document a disparu pendant l'enregistrement de l'échec."
                )
        except Exception:
            logger.exception(
                "Impossible d'enregistrer l'échec du document %s.",
                document_id,
            )
        raise
