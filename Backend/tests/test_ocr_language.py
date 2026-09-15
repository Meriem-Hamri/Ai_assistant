from pathlib import Path

import pytest

from app.extraction import ocr_router, tesseract_reader


def test_french_uses_existing_paddle_reader(monkeypatch):
    calls = []
    monkeypatch.setattr(
        ocr_router,
        "_extract_with_paddle",
        lambda path: calls.append(path) or "texte français",
    )

    assert ocr_router.extract_text_from_image("scan.png") == "texte français"
    assert calls == ["scan.png"]


@pytest.mark.parametrize(
    ("language", "expected_tesseract_language"),
    [("ar", "ara"), ("mixed", "ara+fra")],
)
def test_arabic_modes_use_tesseract(
    monkeypatch,
    tmp_path: Path,
    language,
    expected_tesseract_language,
):
    image = tmp_path / "scan.png"
    image.touch()
    calls = []

    class FakePytesseract:
        class TesseractNotFoundError(Exception):
            pass

        @staticmethod
        def image_to_string(path, *, lang):
            calls.append((path, lang))
            return "  نص عربي  "

    monkeypatch.setattr(tesseract_reader, "_get_pytesseract", lambda: FakePytesseract)

    assert tesseract_reader.extract_text_from_image(str(image), language) == "نص عربي"
    assert calls == [(str(image), expected_tesseract_language)]


@pytest.mark.parametrize("language", ["ar", "mixed"])
def test_router_sends_arabic_modes_to_tesseract(monkeypatch, language):
    calls = []
    monkeypatch.setattr(
        ocr_router,
        "_extract_with_tesseract",
        lambda path, selected: calls.append((path, selected)) or "نص",
    )

    assert ocr_router.extract_text_from_image("scan.png", language) == "نص"
    assert calls == [("scan.png", language)]


def test_tesseract_unavailable_is_reported(monkeypatch, tmp_path: Path):
    image = tmp_path / "scan.png"
    image.touch()

    class FakePytesseract:
        class TesseractNotFoundError(Exception):
            pass

        @staticmethod
        def image_to_string(path, *, lang):
            raise FakePytesseract.TesseractNotFoundError()

    monkeypatch.setattr(tesseract_reader, "_get_pytesseract", lambda: FakePytesseract)

    with pytest.raises(RuntimeError, match="indisponible"):
        tesseract_reader.extract_text_from_image(str(image), "ar")
