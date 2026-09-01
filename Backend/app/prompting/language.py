import re


FRENCH_FALLBACK = "Information non disponible dans les documents."
ARABIC_FALLBACK = "المعلومة غير متوفرة في الوثائق."

_ARABIC_CHARACTER = re.compile(
    r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]"
)
_LATIN_LETTER = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]")


def question_language(question: str) -> str:
    """Détecte seulement si la question est principalement arabe ou latine."""

    arabic_count = len(_ARABIC_CHARACTER.findall(question))
    latin_count = len(_LATIN_LETTER.findall(question))
    return "ar" if arabic_count > latin_count else "fr"


def fallback_for_question(question: str) -> str:
    return ARABIC_FALLBACK if question_language(question) == "ar" else FRENCH_FALLBACK


def response_language_instruction(question: str) -> str:
    if question_language(question) == "ar":
        return (
            "Réponds en arabe, langue principale de la question. "
            "Ne traduis le document que si nécessaire. Fallback exact : "
            f"{ARABIC_FALLBACK}"
        )
    return (
        "Réponds en français, langue de la question. "
        "Ne traduis que si nécessaire. Fallback exact : "
        f"{FRENCH_FALLBACK}"
    )
