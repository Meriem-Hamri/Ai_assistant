from app.documents.processor import DocumentProcessor
from app.metadata.config import MetadataExtractorConfig
from app.metadata.extractor import MetadataExtractor


class FakeLLM:
    def __init__(self, response: str) -> None:
        self.response = response
        self.prompt = ""

    def generate(self, prompt: str) -> str:
        self.prompt = prompt
        return self.response


class SequentialFakeLLM:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.responses.pop(0)


def test_extracts_structured_metadata_from_model_response():
    llm = FakeLLM(
        """```json
        {
          "title": "Contrat de travail",
          "category": "RH",
          "year": 2016,
          "person": "Ahmed El Amrani",
          "department": "Ressources Humaines",
          "document_type": "contrat",
          "tags": ["contrat", "salaire", "contrat"]
        }
        ```"""
    )
    extractor = MetadataExtractor(
        llm=llm,
        config=MetadataExtractorConfig(max_input_characters=100),
    )

    metadata = extractor.extract("Contrat de travail\nAnnée 2016\nSalaire")

    assert metadata.title == "Contrat de travail"
    assert metadata.category == "RH"
    assert metadata.year == 2016
    assert metadata.person == "Ahmed El Amrani"
    assert metadata.tags == ["contrat", "salaire"]
    assert "Retourne uniquement un objet JSON valide" in llm.prompt


def test_falls_back_to_reliable_title_and_year_when_model_fails():
    extractor = MetadataExtractor(
        llm=FakeLLM("ceci n'est pas du JSON"),
    )

    metadata = extractor.extract(
        "Contrat de travail\nDirection des Ressources Humaines\nAnnée 2016"
    )

    assert metadata.title == "Contrat de travail"
    assert metadata.year == 2016
    assert metadata.category is None
    assert metadata.tags == []


def test_manual_metadata_overrides_automatic_metadata():
    merged = DocumentProcessor._merge_business_metadata(
        automatic_metadata={
            "title": "Contrat de travail",
            "category": "RH",
            "year": 2016,
            "person": "Ahmed",
            "department": "Ressources Humaines",
            "document_type": "contrat",
            "tags": ["contrat", "salaire"],
        },
        manual_metadata={
            "title": None,
            "category": "finance",
            "year": None,
            "person": None,
            "department": None,
            "document_type": None,
            "tags": ["paie"],
        },
        manual_tags_provided=True,
    )

    assert merged["title"] == "Contrat de travail"
    assert merged["category"] == "Finance"
    assert merged["year"] == 2016
    assert merged["tags"] == ["paie"]


def test_normalizes_literal_line_breaks_in_metadata_response():
    metadata = MetadataExtractor(
        llm=FakeLLM(
            '{"title": "Guide\\\\ninterne", "tags": []}'
        )
    ).extract("Guide interne")

    assert metadata.title == "Guide interne"


def test_retries_with_a_tags_only_prompt_when_first_response_has_no_tags():
    llm = SequentialFakeLLM(
        [
            '{"title": "Contrat", "year": 2016, "tags": []}',
            '{"tags": ["contrat", "salaire", "rémunération"]}',
        ]
    )

    metadata = MetadataExtractor(llm=llm).extract(
        "Contrat de travail. Le salaire mensuel est fixé à 9500 DH. "
        "La rémunération est versée chaque mois."
        * 3
    )

    assert metadata.tags == ["contrat", "salaire", "rémunération"]
    assert len(llm.prompts) == 2
    assert "Extrais les tags de recherche documentaire" in llm.prompts[1]
