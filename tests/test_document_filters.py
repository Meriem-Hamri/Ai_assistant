from app.vectorstore.filters import DocumentFilters


def test_builds_chroma_filter_for_all_active_criteria():
    where = DocumentFilters(
        category=" finance ",
        year=2016,
        person=" Ahmed ",
        tags=("salaire", "rémunération", "salaire"),
        department="RH",
        document_type="contrat",
    ).to_chroma_where(document_id="document-1")

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
