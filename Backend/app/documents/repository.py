import json
from pathlib import Path


class DocumentRepository:
    """
    Responsable du stockage et de la récupération
    des métadonnées des documents.
    """

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

        if not self._file_path.exists():
            self._write([])

    def save(
        self,
        metadata: dict,
    ) -> None:
        """
        Enregistre les métadonnées d'un document.
        """

        documents = self.get_all()

        documents.append(metadata)

        self._write(documents)

    def get_all(self) -> list[dict]:
        """
        Retourne tous les documents enregistrés.
        """

        try:
            with self._file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                return json.load(file)

        except json.JSONDecodeError:
            return []

    def get_by_id(
        self,
        document_id: str,
    ) -> dict | None:
        """
        Retourne un document à partir de son identifiant.

        Retourne None si le document n'existe pas.
        """

        documents = self.get_all()

        for document in documents:
            if document.get("id") == document_id:
                return document

        return None

    def _write(
        self,
        documents: list[dict],
    ) -> None:
        """
        Écrit les métadonnées dans le fichier JSON.
        """

        with self._file_path.open(
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

    def delete(
        self,
        document_id: str,
    ) -> bool:
        """
        Supprime les métadonnées d'un document.

        Retourne True si le document existait,
        False sinon.
        """

        documents = self.get_all()

        filtered_documents = [
            document
            for document in documents
            if document.get("id") != document_id
        ]

        if len(filtered_documents) == len(documents):
            return False

        self._write(filtered_documents)

        return True