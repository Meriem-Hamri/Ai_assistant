from app.extraction.detector import detect_document_type
from app.extraction.pdf_reader import extract_text_from_pdf
from app.extraction.docx_reader import extract_text_from_docx
from app.extraction.image_reader import extract_text_from_image

from app.models.document import Document


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
        return extract_text_from_image(file_path)

    raise ValueError(f"Type de document non supporté : {document_type}")