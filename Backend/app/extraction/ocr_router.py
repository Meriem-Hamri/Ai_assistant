from app.extraction.ocr_language import DEFAULT_OCR_LANGUAGE, OcrLanguage


def _extract_with_paddle(image_path: str) -> str:
    from app.extraction.ocr_reader import extract_text_from_image

    return extract_text_from_image(image_path)


def _extract_with_tesseract(image_path: str, language: OcrLanguage) -> str:
    from app.extraction.tesseract_reader import extract_text_from_image

    return extract_text_from_image(image_path, language)


def extract_text_from_image(
    image_path: str,
    language: OcrLanguage = DEFAULT_OCR_LANGUAGE,
) -> str:
    """Choisit le moteur OCR sans modifier le chemin Paddle français."""

    if language == "fr":
        return _extract_with_paddle(image_path)
    if language in {"ar", "mixed"}:
        return _extract_with_tesseract(image_path, language)
    raise ValueError(f"Langue OCR non supportée : {language}")
