from pathlib import Path

from paddleocr import PaddleOCR

from app.models.document import Document, DocumentPage


ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang="fr"
)