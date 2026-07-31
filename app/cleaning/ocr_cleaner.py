"""
Nettoyage léger des sorties OCR.
"""

import re


def clean(text: str) -> str:
    """
    Corrige quelques erreurs fréquentes de l'OCR.
    """

    if not text:
        return ""

    corrections = {
        "I'entreprise": "l'entreprise",
        "Ies ": "les ",
        "0bjectif": "Objectif",
    }

    for old, new in corrections.items():
        text = text.replace(old, new)

    # retire les espaces multiples créés par l'OCR
    text = re.sub(r"[ ]{2,}", " ", text)

    return text