from pathlib import Path

from paddleocr import PaddleOCR


ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang="fr",
    enable_mkldnn=False,
    text_detection_model_name="PP-OCRv5_mobile_det",
)


def extract_text_from_image(image_path: str) -> str:
    """
    Extrait le texte d'une image grâce à PaddleOCR.

    Args:
        image_path:
            Chemin vers l'image à analyser.

    Returns:
        Le texte extrait par OCR.

    Raises:
        FileNotFoundError:
            Si l'image n'existe pas.
        ValueError:
            Si l'OCR échoue.
    """

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"L'image '{image_path}' est introuvable."
        )

    try:
        results = ocr.predict(str(path))

        extracted_text = []

        for result in results:
            texts = result["rec_texts"]
            extracted_text.extend(texts)

        return "\n".join(extracted_text).strip()

    except Exception as exc:
        raise ValueError(
            f"Impossible d'extraire le texte de l'image : {exc}"
        ) from exc
