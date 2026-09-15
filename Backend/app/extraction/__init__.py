"""Lecteurs et routage d'extraction documentaire."""

from app.extraction.ocr_language import DEFAULT_OCR_LANGUAGE, OcrLanguage
from app.models.document import Document


def extract_text_from_pdf(
    file_path: str,
    ocr_language: OcrLanguage = DEFAULT_OCR_LANGUAGE,
) -> Document:
    """Conserve l'API historique sans initialiser un moteur OCR à l'import."""

    from app.extraction.pdf_reader import extract_text_from_pdf as extract

    return extract(file_path, ocr_language)
