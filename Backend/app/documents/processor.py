from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from app.cleaning.cleaner import clean_document
from app.extraction.ocr_language import DEFAULT_OCR_LANGUAGE, OcrLanguage
from app.metadata.catalog import canonicalize_exact, merge_reference_values

if TYPE_CHECKING:
    from app.documents.indexer import DocumentIndexer
    from app.metadata.extractor import MetadataExtractor


def extract_document(
    file_path: str,
    ocr_language: OcrLanguage = DEFAULT_OCR_LANGUAGE,
):
    """Charge le pipeline d'extraction uniquement lors du traitement effectif."""

    from app.extraction.extraction_service import extract_document as extract

    return extract(file_path, ocr_language)


@dataclass(frozen=True)
class DocumentProcessingResult:
    """Résultat métier produit par le pipeline documentaire."""

    page_count: int
    chunk_count: int
    title: str | None
    category: str | None
    year: int | None
    person: str | None
    department: str | None
    document_type: str | None
    tags: list[str]


class DocumentProcessor:
    """Exécute de façon synchrone le traitement lourd d'un document."""

    def __init__(
        self,
        indexer: DocumentIndexer,
        metadata_extractor: MetadataExtractor,
    ) -> None:
        self._indexer = indexer
        self._metadata_extractor = metadata_extractor

    def process(
        self,
        *,
        file_path: Path,
        document_id: str,
        filename: str,
        manual_metadata: dict,
        manual_tags_provided: bool,
        reference_values: dict[str, list[str]] | None = None,
        ocr_language: OcrLanguage = DEFAULT_OCR_LANGUAGE,
    ) -> DocumentProcessingResult:
        document = extract_document(str(file_path), ocr_language)

        for page in document.pages:
            page.text = clean_document(page.text)

        document_text = "\n\n".join(page.text for page in document.pages)
        automatic_metadata = self._metadata_extractor.extract(
            document_text
        ).to_dict()
        business_metadata = self._merge_business_metadata(
            automatic_metadata=automatic_metadata,
            manual_metadata=manual_metadata,
            manual_tags_provided=manual_tags_provided,
            reference_values=reference_values,
        )

        document.id = document_id
        document.filename = filename
        document.metadata.update(business_metadata)

        chunks = self._indexer.index(document)

        return DocumentProcessingResult(
            page_count=len(document.pages),
            chunk_count=len(chunks),
            title=business_metadata["title"],
            category=business_metadata["category"],
            year=business_metadata["year"],
            person=business_metadata["person"],
            department=business_metadata["department"],
            document_type=business_metadata["document_type"],
            tags=business_metadata["tags"],
        )

    @staticmethod
    def _merge_business_metadata(
        *,
        automatic_metadata: dict,
        manual_metadata: dict,
        manual_tags_provided: bool,
        reference_values: dict[str, list[str]] | None = None,
    ) -> dict:
        """Les corrections manuelles priment sur l'analyse automatique."""

        merged_metadata = dict(automatic_metadata)

        for key in (
            "title",
            "category",
            "year",
            "person",
            "department",
            "document_type",
        ):
            if manual_metadata[key] is not None:
                merged_metadata[key] = manual_metadata[key]

        if manual_tags_provided:
            merged_metadata["tags"] = manual_metadata["tags"]

        references = reference_values or {
            field: merge_reference_values(field, [])
            for field in ("category", "department", "document_type")
        }
        for field in ("category", "department", "document_type"):
            merged_metadata[field] = canonicalize_exact(
                merged_metadata.get(field), references[field]
            )

        return merged_metadata
