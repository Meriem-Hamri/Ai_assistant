from app.api.schemas.chat import ChatRequest


def test_chat_request_accepts_business_filters():
    request = ChatRequest(
        conversation_id="conversation-1",
        question="Quel était le salaire ?",
        category="finance",
        year=2016,
        person="Ahmed",
        tags=["salaire", "contrat"],
        department="RH",
        document_type="contrat",
    )

    assert request.conversation_id == "conversation-1"
    assert request.category == "finance"
    assert request.year == 2016
    assert request.tags == ["salaire", "contrat"]
