"""
Nettoyage léger des sorties OCR.

Corrige certaines erreurs numériques fréquentes
sans modifier les mots du texte.
"""

import re


def clean(text: str) -> str:
    """
    Corrige les confusions fréquentes entre 'o'/'O' et '0'
    uniquement dans les séquences numériques.

    Exemples :
        5o0   -> 500
        5O0   -> 500
        2ooo  -> 2000
        2OOO  -> 2000
        2 ooo -> 2 000
        2 OOO -> 2 000

    Les mots normaux ne sont pas modifiés.
    """

    if not text:
        return ""

    # --------------------------------------------------
    # 1. Chiffre + o/O + chiffre
    # --------------------------------------------------
    # Exemple :
    # 5o0 -> 500
    # 5O0 -> 500
    text = re.sub(
        r"(?<=\d)[oO](?=\d)",
        "0",
        text,
    )

    # --------------------------------------------------
    # 2. Chiffre + plusieurs o/O
    # --------------------------------------------------
    # Exemple :
    # 2ooo -> 2000
    # 2OOO -> 2000
    text = re.sub(
        r"(?<=\d)[oO]+(?=\s|[.,;:!?)]|$)",
        lambda match: "0" * len(match.group()),
        text,
    )

    # --------------------------------------------------
    # 3. Chiffre + espace + plusieurs o/O
    # --------------------------------------------------
    # Exemple :
    # 2 ooo -> 2 000
    # 2 OOO -> 2 000
    text = re.sub(
        r"(\d)\s+([oO]{2,})(?=\s|[.,;:!?)]|$)",
        lambda match: (
            f"{match.group(1)} "
            f"{'0' * len(match.group(2))}"
        ),
        text,
    )

    return text