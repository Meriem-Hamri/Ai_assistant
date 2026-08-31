from app.extraction.extraction_service import extract_document


print("=" * 50)
print("PDF")
print("=" * 50)

document = extract_document(
    "documents/pdf/img.pdf"
)

print(document)


# print("=" * 50)
# print("DOCX")
# print("=" * 50)

# document = extract_document(
#     "documents/docx/TestWordDoc.doc"
# )

# print(document)


print("=" * 50)
print("IMAGE")
print("=" * 50)

document = extract_document(
    "documents/images/images.jpg"
)

print(document)