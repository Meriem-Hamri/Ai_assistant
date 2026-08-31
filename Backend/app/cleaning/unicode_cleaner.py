"""
Normalisation des caractères Unicode.

Ce module remplace certains caractères typographiques par des
équivalents simples afin d'obtenir un texte plus homogène.
"""

import unicodedata


def clean(text: str) -> str:
    """
    Nettoie les caractères Unicode problématiques.

    Parameters
    ----------
    text : str
        Texte à nettoyer.

    Returns
    -------
    str
        Texte normalisé.
    """

    if not text:
        return ""

    # Décomposition Unicode (ex : ligatures)
    text = unicodedata.normalize("NFKC", text)

    replacements = {
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "–": "-",
        "—": "-",
        "…": "...",
        "\u00A0": " ",   # espace insécable
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text