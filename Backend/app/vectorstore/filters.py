from dataclasses import dataclass


def normalize_document_ids(
    document_ids: list[str] | tuple[str, ...] | None,
) -> tuple[str, ...]:
    """Normalise une sélection documentaire en tuple ordonné et unique."""

    if document_ids is None:
        return ()
    if not isinstance(document_ids, (list, tuple)):
        raise TypeError("document_ids doit être une liste, un tuple ou None.")

    normalized_document_ids: list[str] = []
    for document_id in document_ids:
        if not isinstance(document_id, str):
            raise TypeError("Chaque document_id doit être une chaîne.")
        normalized_document_id = document_id.strip()
        if (
            normalized_document_id
            and normalized_document_id not in normalized_document_ids
        ):
            normalized_document_ids.append(normalized_document_id)

    return tuple(normalized_document_ids)


@dataclass(frozen=True)
class DocumentFilters:
    """Filtres métier appliqués avant la recherche vectorielle."""

    category: str | None = None
    year: int | None = None
    person: str | None = None
    tags: tuple[str, ...] = ()
    department: str | None = None
    document_type: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "category",
            "person",
            "department",
            "document_type",
        ):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise TypeError(f"{field_name} doit être une chaîne ou None.")
            if isinstance(value, str):
                object.__setattr__(self, field_name, value.strip() or None)

        if self.year is not None and not 1000 <= self.year <= 9999:
            raise ValueError("year doit être comprise entre 1000 et 9999.")

        normalized_tags: list[str] = []
        for tag in self.tags:
            if not isinstance(tag, str):
                raise TypeError("Chaque tag doit être une chaîne.")
            normalized_tag = tag.strip()
            if normalized_tag and normalized_tag not in normalized_tags:
                normalized_tags.append(normalized_tag)
        object.__setattr__(self, "tags", tuple(normalized_tags))

    @property
    def is_empty(self) -> bool:
        return not any(
            (
                self.category,
                self.year,
                self.person,
                self.tags,
                self.department,
                self.document_type,
            )
        )

    def to_chroma_where(
        self,
        document_ids: list[str] | tuple[str, ...] | None = None,
    ) -> dict | None:
        """Construit une clause Chroma : tous les critères sont requis."""

        clauses: list[dict] = []
        normalized_document_ids = normalize_document_ids(document_ids)

        if len(normalized_document_ids) == 1:
            clauses.append({"document_id": normalized_document_ids[0]})
        elif normalized_document_ids:
            clauses.append({
                "document_id": {"$in": list(normalized_document_ids)},
            })

        for key in (
            "category",
            "year",
            "person",
            "department",
            "document_type",
        ):
            value = getattr(self, key)
            if value is not None:
                clauses.append({key: value})

        for tag in self.tags:
            clauses.append({f"tag_{self._tag_key(tag)}": True})

        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    @staticmethod
    def _tag_key(tag: str) -> str:
        return "".join(
            character.lower() if character.isalnum() else "_"
            for character in tag
        ).strip("_")
