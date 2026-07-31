"""
Nettoyage principal des documents.
"""

from app.cleaning import (
    unicode_cleaner,
    whitespace_cleaner,
    pdf_cleaner,
    ocr_cleaner,
)


def clean_document(text: str) -> str:
    """
    Exécute l'ensemble de la chaîne de nettoyage.
    """

    text = unicode_cleaner.clean(text)
    text = whitespace_cleaner.clean(text)
    text = pdf_cleaner.clean(text)
    text = ocr_cleaner.clean(text)

    return text