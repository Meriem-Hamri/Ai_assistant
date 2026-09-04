from __future__ import annotations

import re
import unicodedata


FUZZY_STRONG_THRESHOLD = 0.84
FUZZY_POSSIBLE_THRESHOLD = 0.72

INITIAL_VOCABULARY: dict[str, tuple[str, ...]] = {
    "category": (
        "Finance", "Ressources humaines", "Informatique", "Juridique",
        "Commercial", "Marketing", "Formation", "Administration", "Opérations",
    ),
    "department": (
        "Direction générale", "Finance", "Ressources humaines", "Informatique",
        "Commercial", "Marketing", "Juridique", "Opérations",
    ),
    "document_type": (
        "Rapport", "Contrat", "Procédure", "Guide", "Facture",
        "Présentation", "CV", "Note", "Politique",
    ),
}


def clean_display_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned or None


def normalized_name(value: str | None) -> str:
    cleaned = clean_display_value(value)
    if cleaned is None:
        return ""
    decomposed = unicodedata.normalize("NFKD", cleaned)
    without_accents = "".join(
        character for character in decomposed
        if not unicodedata.combining(character)
    )
    return without_accents.casefold()


def merge_reference_values(field: str, existing_values: list[str] | tuple[str, ...]) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for value in (*existing_values, *INITIAL_VOCABULARY[field]):
        cleaned = clean_display_value(value)
        key = normalized_name(cleaned)
        if cleaned and key not in seen:
            seen.add(key)
            values.append(cleaned)
    return values


def canonicalize_exact(value: str | None, candidates: list[str] | tuple[str, ...]) -> str | None:
    cleaned = clean_display_value(value)
    if cleaned is None:
        return None
    key = normalized_name(cleaned)
    for candidate in candidates:
        if normalized_name(candidate) == key:
            return candidate
    return cleaned


def find_fuzzy_match(value: str, candidates: list[str] | tuple[str, ...]) -> tuple[str, float] | None:
    key = normalized_name(value)
    if not key:
        return None

    def similarity(candidate: str) -> float:
        other = normalized_name(candidate)
        if key == other:
            return 1.0
        previous = list(range(len(other) + 1))
        for index, left_character in enumerate(key, start=1):
            current = [index]
            for other_index, right_character in enumerate(other, start=1):
                current.append(min(
                    current[-1] + 1,
                    previous[other_index] + 1,
                    previous[other_index - 1] + (left_character != right_character),
                ))
            previous = current
        return 1 - previous[-1] / max(len(key), len(other))

    ranked = sorted(
        (
            (candidate, similarity(candidate))
            for candidate in candidates
        ),
        key=lambda item: (-item[1], normalized_name(item[0])),
    )
    if not ranked or ranked[0][1] < FUZZY_POSSIBLE_THRESHOLD:
        return None
    return ranked[0]
