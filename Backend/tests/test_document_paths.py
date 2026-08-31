from pathlib import Path

from app.documents import paths


def test_resolve_document_path_preserves_absolute_path(tmp_path: Path):
    file_path = tmp_path / "document.pdf"

    assert paths.resolve_document_path(str(file_path)) == file_path


def test_resolve_document_path_supports_backend_relative_path(
    monkeypatch,
    tmp_path: Path,
):
    backend_dir = tmp_path / "Backend"
    file_path = backend_dir / "documents" / "document.pdf"
    file_path.parent.mkdir(parents=True)
    file_path.touch()
    monkeypatch.setattr(paths, "BACKEND_DIR", backend_dir)
    monkeypatch.setattr(paths, "PROJECT_ROOT", tmp_path)

    assert paths.resolve_document_path("documents/document.pdf") == file_path


def test_resolve_document_path_supports_historical_project_relative_path(
    monkeypatch,
    tmp_path: Path,
):
    backend_dir = tmp_path / "Backend"
    monkeypatch.setattr(paths, "BACKEND_DIR", backend_dir)
    monkeypatch.setattr(paths, "PROJECT_ROOT", tmp_path)

    result = paths.resolve_document_path("Backend/documents/document.pdf")

    assert result == tmp_path / "Backend" / "documents" / "document.pdf"
