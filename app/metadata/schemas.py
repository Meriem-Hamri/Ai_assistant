from dataclasses import dataclass, field
import re
from typing import Any


@dataclass(frozen=True)
class ExtractedDocumentMetadata:
    """Métadonnées métier déduites du contenu d'un document."""

    title: str | None = None
    category: str | None = None
    year: int | None = None
    person: str | None = None
    department: str | None = None
    document_type: str | None = None
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_mapping(
        cls,
        data: dict[str, Any],
    ) -> "ExtractedDocumentMetadata":
        """Valide et normalise la réponse JSON du modèle local."""

        def text(key: str) -> str | None:
            value = data.get(key)
            if not isinstance(value, str):
                return None
            value = re.sub(r"\s+", " ", value.replace("\\n", " ")).strip()
            return value or None

        year = data.get("year")
        if isinstance(year, bool) or not isinstance(year, int):
            year = None
        elif not 1000 <= year <= 9999:
            year = None

        tags: list[str] = []
        raw_tags = data.get("tags", [])
        if isinstance(raw_tags, list):
            for tag in raw_tags:
                if not isinstance(tag, str):
                    continue
                normalized_tag = tag.strip()
                if normalized_tag and normalized_tag not in tags:
                    tags.append(normalized_tag)

        return cls(
            title=text("title"),
            category=text("category"),
            year=year,
            person=text("person"),
            department=text("department"),
            document_type=text("document_type"),
            tags=tags,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "category": self.category,
            "year": self.year,
            "person": self.person,
            "department": self.department,
            "document_type": self.document_type,
            "tags": list(self.tags),
        }
