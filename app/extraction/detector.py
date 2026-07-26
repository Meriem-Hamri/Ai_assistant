from pathlib import Path

from app.models.document import Document
from app.extraction.pdf_reader import extract_text_from_pdf
from app.extraction.docx_reader import extract_text_from_docx


SUPPORTED_EXTENSIONS = {
    ".pdf": extract_text_from_pdf,
    ".docx": extract_text_from_docx,
}


def load_document(file_path: str) -> Document:
    """
    Charge un document en appelant automatiquement
    le lecteur adapté au format.
    """

    path = Path(file_path)

    extension = path.suffix.lower()

    reader = SUPPORTED_EXTENSIONS.get(extension)

    if reader is None:
        raise ValueError(
            f"Format non supporté : {extension}"
        )

    return reader(file_path)