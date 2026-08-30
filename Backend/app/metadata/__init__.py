"""Extraction des métadonnées métier d'un document."""

from app.metadata.extractor import MetadataExtractor
from app.metadata.schemas import ExtractedDocumentMetadata

__all__ = ["ExtractedDocumentMetadata", "MetadataExtractor"]
