from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


def resolve_document_path(stored_path: str) -> Path:
    """Résout les fichiers backend et les chemins historiques du projet."""

    path = Path(stored_path)
    if path.is_absolute():
        return path

    backend_path = BACKEND_DIR / path
    if backend_path.exists():
        return backend_path

    return PROJECT_ROOT / path
