from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang="fr",
)

result = ocr.predict("documents/images/images.jpg")

print(result)
print(type(result))

if len(result) > 0:
    print(type(result[0]))
    print(result[0])