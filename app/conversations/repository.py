import json
from pathlib import Path


class ConversationRepository:
    """
    Responsable du stockage et de la récupération
    des métadonnées des conversations.
    """

    def __init__(
        self,
        file_path: Path = Path(
            "data/conversations.json"
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
        conversation: dict,
    ) -> None:
        """
        Enregistre une conversation.
        """

        conversations = self.get_all()

        conversations.append(conversation)

        self._write(conversations)

    def get_all(self) -> list[dict]:
        """
        Retourne toutes les conversations.
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
        conversations: list[dict],
    ) -> None:
        """
        Écrit les conversations dans le fichier JSON.
        """

        with self._file_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                conversations,
                file,
                ensure_ascii=False,
                indent=4,
            )