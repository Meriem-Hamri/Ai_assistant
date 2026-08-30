from app.extraction.detector import detect_document_type
from app.extraction.pdf_reader import extract_text_from_pdf
from app.extraction.docx_reader import extract_text_from_docx
from app.extraction.image_reader import extract_text_from_image
from pathlib import Path

from app.models.document import Document, DocumentPage

from app.models.document import Document
import io


def extract_document(file_path: str) -> Document:
    """
    Détecte automatiquement le type du document
    puis appelle le lecteur approprié.

    Returns:
        Document
    """

    document_type = detect_document_type(file_path)

    if document_type == "pdf":
        return extract_text_from_pdf(file_path)

    elif document_type == "docx":
        return extract_text_from_docx(file_path)

    elif document_type == "image":
        text = extract_text_from_image(file_path)

        document = Document(
            filename=Path(file_path).name
        )

        document.pages.append(
            DocumentPage(
                page_number=1,
                text=text,
            )
        )

        return document

    raise ValueError(f"Type de document non supporté : {document_type}")