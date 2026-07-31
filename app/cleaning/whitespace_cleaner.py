"""
Nettoyage des espaces.
"""

import re


def clean(text: str) -> str:
    """
    Nettoie les espaces inutiles.

    - supprime les tabulations
    - remplace plusieurs espaces par un seul
    - limite les lignes vides à une seule
    """

    if not text:
        return ""

    text = text.replace("\t", " ")

    text = re.sub(r"[ ]{2,}", " ", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()