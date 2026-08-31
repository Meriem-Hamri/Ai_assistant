"""
Nettoyage principal des documents.
"""

from app.cleaning import ocr_cleaner, pdf_cleaner, unicode_cleaner
from app.cleaning import (
    whitespace_cleaner,
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