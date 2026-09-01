from app.vectorstore.filters import DocumentFilters


def test_builds_chroma_filter_for_all_active_criteria():
    where = DocumentFilters(
        category=" finance ",
        year=2016,
        person=" Ahmed ",
        tags=("salaire", "rémunération", "salaire"),
        department="RH",
        document_type="contrat",
    ).to_chroma_where(document_ids=("document-1",))

    assert where == {
        "$and": [
            {"document_id": "document-1"},
            {"category": "finance"},
            {"year": 2016},
            {"person": "Ahmed"},
            {"department": "RH"},
            {"document_type": "contrat"},
            {"tag_salaire": True},
            {"tag_rémunération": True},
        ]
    }


def test_returns_no_filter_when_no_criteria_are_active():
    assert DocumentFilters().to_chroma_where() is None


def test_empty_document_ids_add_no_document_filter():
    assert DocumentFilters().to_chroma_where(document_ids=[]) is None


def test_one_document_id_uses_an_exact_filter():
    assert DocumentFilters().to_chroma_where(document_ids=["A"]) == {
        "document_id": "A",
    }


def test_multiple_document_ids_use_in_filter():
    assert DocumentFilters().to_chroma_where(document_ids=["A", "B"]) == {
        "document_id": {"$in": ["A", "B"]},
    }


def test_multiple_document_ids_and_category_are_combined_with_and():
    where = DocumentFilters(category="finance").to_chroma_where(
        document_ids=["A", "B"],
    )

    assert where == {
        "$and": [
            {"document_id": {"$in": ["A", "B"]}},
            {"category": "finance"},
        ]
    }


def test_multiple_document_ids_preserve_tag_filters():
    where = DocumentFilters(tags=("salaire", "contrat")).to_chroma_where(
        document_ids=["A", "B"],
    )

    assert where == {
        "$and": [
            {"document_id": {"$in": ["A", "B"]}},
            {"tag_salaire": True},
            {"tag_contrat": True},
        ]
    }


def test_document_ids_are_trimmed_and_deduplicated_in_order():
    where = DocumentFilters().to_chroma_where(
        document_ids=[" A ", "", "A", " B ", "  "],
    )

    assert where == {"document_id": {"$in": ["A", "B"]}}


def test_document_ids_must_contain_strings():
    import pytest

    with pytest.raises(TypeError, match="document_id"):
        DocumentFilters().to_chroma_where(document_ids=["A", 2])
