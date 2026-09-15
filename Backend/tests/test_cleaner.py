from app.cleaning.unicode_cleaner import clean as unicode_clean
from app.cleaning.whitespace_cleaner import clean as whitespace_clean
from app.cleaning.pdf_cleaner import clean as pdf_clean
from app.cleaning.ocr_cleaner import clean as ocr_clean
from app.cleaning.cleaner import clean_document


def test_unicode_cleaner():
    assert unicode_clean("ï¬") == "fi"
    assert unicode_clean("â€œBonjourâ€") == '"Bonjour"'


def test_whitespace_cleaner():
    assert whitespace_clean("Bonjour    monde") == "Bonjour monde"
    assert whitespace_clean("A\n\n\nB") == "A\n\nB"


def test_pdf_cleaner():
    assert pdf_clean("informa-\ntion") == "information"


def test_ocr_cleaner():
    assert ocr_clean("I'entreprise") == "l'entreprise"
    assert ocr_clean("0bjectif") == "Objectif"


def test_full_cleaner():
    text = "â€œinforma-\ntionâ€"
    assert clean_document(text) == '"information"'


def test_full_cleaner_preserves_arabic_letters_and_diacritics():
    text = "  مَرْحَبًا   بالعالم؟  "

    assert clean_document(text) == "مَرْحَبًا بالعالم؟"
