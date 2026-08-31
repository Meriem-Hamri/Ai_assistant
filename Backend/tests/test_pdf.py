from app.extraction.pdf_reader import extract_pdf_text

document = extract_pdf_text("documents/pdf/50_pages.pdf")

print("=" * 50)
print(document.filename)

for page in document.pages:
    print(f"\nPage {page.page_number}")
    print("-" * 30)
    print(page.text)