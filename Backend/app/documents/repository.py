import json
from pathlib import Path
from threading import RLock


class DocumentRepository:
    """
    Responsable du stockage et de la récupération
    des métadonnées des documents.

    Les accès au fichier JSON sont protégés contre
    les modifications concurrentes dans le processus.
    """

    _lock = RLock()

    def __init__(
        self,
        file_path: Path = Path(
            "data/documents_metadata.json"
        ),
    ) -> None:
        self._file_path = file_path

        self._file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self._lock:
            if not self._file_path.exists():
                self._write([])

    def save(
        self,
        metadata: dict,
    ) -> None:
        """
        Enregistre les métadonnées d'un document.
        """

        with self._lock:
            documents = self._read()

            documents.append(metadata)

            self._write(documents)

    def get_all(self) -> list[dict]:
        """
        Retourne tous les documents enregistrés.
        """

        with self._lock:
            return self._read()

    def get_by_id(
        self,
        document_id: str,
    ) -> dict | None:
        """
        Retourne un document à partir de son identifiant.
        """

        with self._lock:
            documents = self._read()

            for document in documents:
                if document.get("id") == document_id:
                    return document

        return None

    def delete(
        self,
        document_id: str,
    ) -> bool:
        """
        Supprime les métadonnées d'un document.

        Retourne True si le document existait,
        False sinon.
        """

        with self._lock:
            documents = self._read()

            filtered_documents = [
                document
                for document in documents
                if document.get("id") != document_id
            ]

            if len(filtered_documents) == len(documents):
                return False

            self._write(filtered_documents)

            return True

    def _read(self) -> list[dict]:
        """
        Lit le fichier JSON.

        Doit être appelée sous protection du lock.
        """

        try:
            with self._file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                return json.load(file)

        except json.JSONDecodeError:
            return []

    def _write(
        self,
        documents: list[dict],
    ) -> None:
        """
        Écrit les métadonnées de manière atomique.

        Doit être appelée sous protection du lock.
        """

        temporary_path = self._file_path.with_suffix(
            ".tmp"
        )

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                documents,
                file,
                ensure_ascii=False,
                indent=4,
                default=str,
            )

        temporary_path.replace(
            self._file_path
        )