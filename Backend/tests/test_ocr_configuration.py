import importlib.util
import sys
from pathlib import Path
from types import ModuleType

def test_readers_share_one_minimally_configured_paddleocr(monkeypatch):
    calls = []
    paddleocr = ModuleType("paddleocr")

    def fake_paddleocr(**kwargs):
        calls.append(kwargs)
        return object()

    paddleocr.PaddleOCR = fake_paddleocr
    monkeypatch.setitem(sys.modules, "paddleocr", paddleocr)

    extraction_path = Path(__file__).parents[1] / "app/extraction"
    ocr_reader_spec = importlib.util.spec_from_file_location(
        "app.extraction.ocr_reader",
        extraction_path / "ocr_reader.py",
    )
    ocr_reader = importlib.util.module_from_spec(ocr_reader_spec)
    monkeypatch.setitem(
        sys.modules,
        "app.extraction.ocr_reader",
        ocr_reader,
    )
    ocr_reader_spec.loader.exec_module(ocr_reader)

    image_reader_spec = importlib.util.spec_from_file_location(
        "test_image_reader_configuration",
        extraction_path / "image_reader.py",
    )
    image_reader = importlib.util.module_from_spec(image_reader_spec)
    image_reader_spec.loader.exec_module(image_reader)

    assert calls == [
        {
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
            "lang": "fr",
            "enable_mkldnn": False,
            "text_detection_model_name": "PP-OCRv5_mobile_det",
        }
    ]
    assert image_reader.ocr is ocr_reader.ocr
