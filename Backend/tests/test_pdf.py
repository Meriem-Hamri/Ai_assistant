from pathlib import Path

from app.extraction.pdf_reader import extract_text_from_pdf


def test_extract_text_from_pdf():
    file_path = Path("documents/pdf/final.pdf")

    document = extract_text_from_pdf(str(file_path))

    assert document.filename == file_path.name
    assert len(document.pages) > 0