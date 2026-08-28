from pathlib import Path

from app.extraction.extraction_service import extract_document


PDF_PATH = Path(
    "documents/pdf/DOCUMENT_DE_TEST_ASSISTANT_RAG.pdf"
)


def test_real_pdf_extraction():

    document = extract_document(
        str(PDF_PATH)
    )

    assert document is not None

    assert document.filename == PDF_PATH.name

    assert len(document.pages) > 0

    print("\n======================================")
    print("DOCUMENT")
    print("======================================")
    print(f"Nom       : {document.filename}")
    print(f"Pages     : {len(document.pages)}")
    print(f"Métadonnées : {document.metadata}")

    for page in document.pages:

        print(
            f"\n--- PAGE {page.page_number} ---"
        )

        print(page.text[:1000])

        assert isinstance(
            page.text,
            str
        )