from dataclasses import dataclass

from app.extraction.ocr_language import DEFAULT_OCR_LANGUAGE, OcrLanguage


@dataclass(frozen=True)
class DocumentProcessingInput:
    """Données persistées nécessaires au traitement d'un document."""

    id: str
    filename: str
    path: str
    status: str
    title: str | None
    category: str | None
    year: int | None
    person: str | None
    department: str | None
    document_type: str | None
    tags: list[str] | None
    ocr_language: OcrLanguage = DEFAULT_OCR_LANGUAGE
