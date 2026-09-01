class CeleryDocumentProcessingDispatcher:
    """Publie les traitements de documents dans la file Celery."""

    def enqueue(self, document_id: str) -> None:
        # L'import tardif évite de configurer Celery au démarrage de FastAPI.
        from app.tasks.documents import process_document

        process_document.delay(document_id)
