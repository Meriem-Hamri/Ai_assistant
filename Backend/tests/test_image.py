from app.extraction.image_reader import extract_text_from_image


document = extract_text_from_image(
    "documents/images/images.jpg"
)


print("Fichier :", document.filename)

for page in document.pages:
    print("Page :", page.page_number)
    print(page.text)