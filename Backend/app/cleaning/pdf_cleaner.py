"""
Nettoyage spécifique aux PDF.
"""

import re


def clean(text: str) -> str:
    """
    Corrige les coupures de mots en fin de ligne.

    Exemple
    --------
    informa-
    tion

    devient

    information
    """

    if not text:
        return ""

    # mot-
    # suivant
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    return text