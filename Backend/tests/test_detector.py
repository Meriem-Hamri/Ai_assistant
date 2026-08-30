from app.extraction.detector import load_document

document = load_document("documents/pdf/final.pdf")

print(document.filename)

for page in document.pages:
    print(page.page_number)