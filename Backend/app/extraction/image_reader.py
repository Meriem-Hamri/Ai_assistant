from pathlib import Path

from app.extraction.ocr_language import DEFAULT_OCR_LANGUAGE, OcrLanguage
from app.extraction.ocr_router import extract_text_from_image as extract_ocr_text
from app.models.document import Document, DocumentPage


def extract_text_from_image(
    file_path: str,
    ocr_language: OcrLanguage = DEFAULT_OCR_LANGUAGE,
) -> Document:
    """
    Extrait le texte d'une image avec le moteur OCR sélectionné.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"L'image '{file_path}' est introuvable."
        )

    try:
        text = extract_ocr_text(str(path), ocr_language)

        document = Document(
            filename=path.name
        )

        document.pages.append(
            DocumentPage(
                page_number=1,
                text=text
            )
        )

        return document

    except Exception as e:
        raise ValueError(
            f"Impossible de lire l'image : {e}"
        )
