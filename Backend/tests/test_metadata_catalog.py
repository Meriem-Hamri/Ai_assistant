import pytest

from app.metadata.catalog import (
    FUZZY_STRONG_THRESHOLD,
    canonicalize_exact,
    find_fuzzy_match,
    merge_reference_values,
    normalized_name,
)


@pytest.mark.parametrize("value", ["finance", " FINANCE ", "  FiNaNcE  "])
def test_exact_normalization_reuses_finance(value):
    options = merge_reference_values("category", [])
    assert canonicalize_exact(value, options) == "Finance"


@pytest.mark.parametrize("value", ["finnce", "finanse"])
def test_fuzzy_typo_suggests_finance(value):
    match = find_fuzzy_match(value, merge_reference_values("category", []))
    assert match is not None
    assert match[0] == "Finance"
    assert match[1] >= FUZZY_STRONG_THRESHOLD


def test_semantically_related_value_is_not_fuzzy_match():
    assert find_fuzzy_match("Comptabilité", ["Finance"]) is None


def test_existing_canonical_value_wins_and_accents_are_ignored():
    options = merge_reference_values("category", ["  CYBERDÉFENSE ", "finance"])
    assert options[:2] == ["CYBERDÉFENSE", "finance"]
    assert canonicalize_exact("cyberdefense", options) == "CYBERDÉFENSE"
    assert canonicalize_exact("FINANCE", options) == "finance"
    assert normalized_name("  Cyberdéfense ") == "cyberdefense"


def test_tags_are_deduplicated_case_and_accent_insensitively():
    from app.documents.service import DocumentService

    metadata = DocumentService._build_business_metadata(
        title=None, category=None, year=None, person=None, department=None,
        document_type=None, tags=[" Audit ", "audit", "Équipe", "equipe"],
    )
    assert metadata["tags"] == ["Audit", "Équipe"]


def test_service_options_prefer_existing_postgresql_values():
    from app.documents.service import DocumentService

    class Repository:
        def get_distinct_metadata_values(self):
            return {
                "category": ["finance", "Cyberdéfense"],
                "department": [],
                "document_type": [],
            }

    service = DocumentService(Repository(), vector_store=None, dispatcher=None)
    options = service.get_metadata_options()

    assert options["category"][:2] == ["finance", "Cyberdéfense"]
    assert options["category"].count("finance") == 1
