from pathlib import Path

from app.extraction.ocr_language import OcrLanguage


TESSERACT_LANGUAGE_CODES: dict[OcrLanguage, str] = {
    "fr": "fra",
    "ar": "ara",
    "mixed": "ara+fra",
}


def _get_pytesseract():
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError("pytesseract n'est pas installé.") from exc
    return pytesseract


def extract_text_from_image(
    image_path: str,
    language: OcrLanguage,
) -> str:
    """Extrait une image avec Tesseract et les packs linguistiques demandés."""

    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"L'image '{image_path}' est introuvable.")

    if language not in {"ar", "mixed"}:
        raise ValueError("Tesseract est réservé aux langues OCR 'ar' et 'mixed'.")

    pytesseract = _get_pytesseract()
    try:
        return pytesseract.image_to_string(
            str(path),
            lang=TESSERACT_LANGUAGE_CODES[language],
        ).strip()
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError("Tesseract est indisponible sur le worker.") from exc
    except Exception as exc:
        raise ValueError(
            f"Impossible d'extraire le texte arabe de l'image : {exc}"
        ) from exc

