import pytest

from app.extraction.detector import detect_document_type


def test_detect_pdf():
    assert detect_document_type("document.pdf") == "pdf"


def test_detect_docx():
    assert detect_document_type("document.docx") == "docx"


def test_detect_image():
    assert detect_document_type("image.png") == "image"


def test_unsupported_extension():
    with pytest.raises(ValueError):
        detect_document_type("document.txt")