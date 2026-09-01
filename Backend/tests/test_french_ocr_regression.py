import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
from PIL import Image

from app.cleaning.cleaner import clean_document
from app.extraction.pdf_reader import _ocr_dpi


def load_ocr_reader(monkeypatch):
    calls = []
    paddleocr = ModuleType("paddleocr")

    class FakeOCR:
        def predict(self, image):
            calls.append(image)
            return [
                {
                    "rec_texts": [
                        "Le salaire mensuel brut est fixe a 9 500 "
                        "dirhams marocains.",
                        "Une prime exceptionnelle de performance.",
                    ]
                }
            ]

    paddleocr.PaddleOCR = lambda **kwargs: FakeOCR()
    monkeypatch.setitem(sys.modules, "paddleocr", paddleocr)

    module_path = (
        Path(__file__).parents[1] / "app/extraction/ocr_reader.py"
    )
    spec = importlib.util.spec_from_file_location(
        "test_french_ocr_reader",
        module_path,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, calls


def test_reconstruction_preserves_word_spaces_and_grouped_number(monkeypatch):
    reader, _ = load_ocr_reader(monkeypatch)

    text = reader.reconstruct_text(
        [
            {
                "rec_texts": [
                    "Le salaire mensuel brut est fixe a 9 500 dirhams.",
                    "Une prime exceptionnelle de performance.",
                ]
            }
        ]
    )

    assert text.splitlines() == [
        "Le salaire mensuel brut est fixe a 9 500 dirhams.",
        "Une prime exceptionnelle de performance.",
    ]


def test_french_reader_preprocesses_without_changing_reconstructed_text(
    monkeypatch,
    tmp_path: Path,
):
    reader, calls = load_ocr_reader(monkeypatch)
    image_path = tmp_path / "scan.png"
    Image.new("RGB", (20, 20), "white").save(image_path)

    text = reader.extract_text_from_image(str(image_path))

    assert "9 500 dirhams" in text
    assert isinstance(calls[0], np.ndarray)
    assert calls[0].shape == (20, 20, 3)
    assert set(np.unique(calls[0])).issubset({0, 255})


def test_cleaning_preserves_correct_french_amount_and_arabic_text():
    french = "Le salaire mensuel brut est fixe a 9 500 dirhams."
    arabic = "المعلومة غير متوفرة في الوثائق."

    assert clean_document(french) == french
    assert clean_document(arabic) == arabic


def test_only_french_pdf_ocr_uses_higher_resolution():
    assert _ocr_dpi("fr") == 250
    assert _ocr_dpi("ar") == 200
    assert _ocr_dpi("mixed") == 200
