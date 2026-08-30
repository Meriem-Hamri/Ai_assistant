import re


def split_into_paragraphs(text: str) -> list[str]:
    """
    Découpe un texte en paragraphes.

    Les paragraphes sont séparés par une ou plusieurs lignes vides.

    Args:
        text: texte à découper.

    Returns:
        Liste des paragraphes.
    """

    paragraphs = re.split(r"\n\s*\n", text)

    return paragraphs

def clean_paragraphs(paragraphs: list[str]) -> list[str]:
    """
    Nettoie une liste de paragraphes.

    - supprime les espaces inutiles ;
    - supprime les paragraphes vides.

    Args:
        paragraphs: liste des paragraphes.

    Returns:
        Liste nettoyée.
    """

    cleaned = []

    for paragraph in paragraphs:

        paragraph = paragraph.strip()

        if paragraph:
            cleaned.append(paragraph)

    return cleaned

def split_large_paragraph(
    paragraph: str,
    max_length: int,
) -> list[str]:
    """
    Découpe un paragraphe trop long sans couper les mots.

    Args:
        paragraph: paragraphe à découper.
        max_length: taille maximale d'un chunk.

    Returns:
        Liste de morceaux.
    """

    words = paragraph.split()

    chunks = []

    current = ""

    for word in words:

        candidate = (
            word
            if not current
            else current + " " + word
        )

        if len(candidate) <= max_length:
            current = candidate

        else:
            chunks.append(current)
            current = word

    if current:
        chunks.append(current)

    return chunks

def merge_small_paragraphs(
    paragraphs: list[str],
    min_length: int,
) -> list[str]:
    """
    Fusionne les paragraphes trop petits afin
    d'obtenir des chunks plus riches.

    Args:
        paragraphs: liste des paragraphes.
        min_length: taille minimale souhaitée.

    Returns:
        Liste des paragraphes fusionnés.
    """

    if not paragraphs:
        return []

    merged = []

    current = paragraphs[0]

    for paragraph in paragraphs[1:]:

        if len(current) < min_length:
            current += "\n\n" + paragraph

        else:
            merged.append(current)
            current = paragraph

    merged.append(current)

    return merged