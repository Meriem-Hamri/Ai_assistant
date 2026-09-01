from pathlib import Path

import numpy as np
from paddleocr import PaddleOCR
from PIL import Image, ImageOps


ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang="fr",
    enable_mkldnn=False,
    text_detection_model_name="PP-OCRv5_mobile_det",
)


def _otsu_threshold(histogram: list[int]) -> int:
    """Calcule un seuil de binarisation adapté à l'image courante."""

    total = sum(histogram)
    weighted_sum = sum(index * count for index, count in enumerate(histogram))
    background_count = 0
    background_sum = 0
    best_threshold = 0
    best_variance = -1.0

    for threshold, count in enumerate(histogram):
        background_count += count
        if background_count == 0:
            continue

        foreground_count = total - background_count
        if foreground_count == 0:
            break

        background_sum += threshold * count
        background_mean = background_sum / background_count
        foreground_mean = (
            weighted_sum - background_sum
        ) / foreground_count
        variance = (
            background_count
            * foreground_count
            * (background_mean - foreground_mean) ** 2
        )

        if variance > best_variance:
            best_variance = variance
            best_threshold = threshold

    return best_threshold


def _prepare_image(image_path: Path) -> np.ndarray:
    """Améliore génériquement le contraste avant l'OCR français."""

    with Image.open(image_path) as image:
        grayscale = ImageOps.grayscale(image)
        threshold = _otsu_threshold(grayscale.histogram())
        binary = grayscale.point(
            lambda pixel: 255 if pixel > threshold else 0
        )
        return np.asarray(binary.convert("RGB"))


def reconstruct_text(results) -> str:
    """Reconstruit les lignes Paddle sans altérer leurs espaces internes."""

    lines: list[str] = []
    for result in results:
        lines.extend(result["rec_texts"])
    return "\n".join(lines).strip()


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
        results = ocr.predict(_prepare_image(path))
        return reconstruct_text(results)

    except Exception as exc:
        raise ValueError(
            f"Impossible d'extraire le texte de l'image : {exc}"
        ) from exc
