from app.extraction.docx_reader import extract_text_from_docx

document = extract_text_from_docx("documents/docx/HAMRI_MERIEM_Demande_de_Stage.docx")

print("=" * 50)
print(document.filename)

for page in document.pages:
    print(f"\nPage {page.page_number}")
    print("-" * 30)
    print(page.text)