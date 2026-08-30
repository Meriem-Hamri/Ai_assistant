"""Point d'entrée de compatibilité pour lancer l'API depuis la racine."""

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent / "Backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.api.main import app


__all__ = ["app"]
