from pathlib import Path


PDF_EXTENSIONS = {".pdf"}

DOCX_EXTENSIONS = {".docx",".doc"}

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tiff",
    ".webp",
}


def detect_document_type(file_path: str) -> str:

    extension = Path(file_path).suffix.lower()

    if extension in PDF_EXTENSIONS:
        return "pdf"

    if extension in DOCX_EXTENSIONS:
        return "docx"

    if extension in IMAGE_EXTENSIONS:
        return "image"

    raise ValueError(
        f"Extension non supportée : {extension}"
    )