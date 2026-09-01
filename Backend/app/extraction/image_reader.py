from pathlib import Path

from app.extraction.ocr_reader import ocr
from app.models.document import Document, DocumentPage


def extract_text_from_image(file_path: str) -> Document:
    """
    Extrait le texte d'une image grâce à PaddleOCR.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"L'image '{file_path}' est introuvable."
        )

    try:
        results = ocr.predict(str(path))

        extracted_text = []

        for result in results:
            texts = result["rec_texts"]

            extracted_text.extend(texts)

        text = "\n".join(extracted_text)

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
