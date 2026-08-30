from app.extraction.pdf_reader import extract_text_from_pdf


pdf_path = "documents/pdf/final.pdf"

document = extract_text_from_pdf(pdf_path)

print()
print("=" * 70)
print("RESULTAT")
print("=" * 70)

print("Nom :", document.filename)
print("Nombre de pages :", len(document.pages))

for page in document.pages:
    print()
    print("-" * 70)
    print(f"PAGE {page.page_number}")
    print("-" * 70)
    print(page.text[:1000])