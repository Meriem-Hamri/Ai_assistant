from app.chat.service import ChatService
from app.rag.response import RAGResponse, Source


class FakeRAGPipeline:
    def answer(self, **kwargs):
        self.received_kwargs = kwargs
        return RAGResponse(
            answer="Le salaire est de 9 500 DH.",
            sources=[
                Source(
                    document_id="document-1",
                    document_name="contrat.pdf",
                    page_number=4,
                    chunk_id="chunk-4",
                    excerpt="Le salaire mensuel brut est fixé à 9 500 DH.",
                    distance=0.12,
                )
            ],
        )


def test_chat_service_returns_clickable_source_data():
    service = ChatService(FakeRAGPipeline())

    response = service.send_message("Quel est le salaire ?")

    assert response.answer == "Le salaire est de 9 500 DH."
    assert response.sources[0].model_dump() == {
        "document_id": "document-1",
        "document_name": "contrat.pdf",
        "page_number": 4,
        "chunk_id": "chunk-4",
        "excerpt": "Le salaire mensuel brut est fixé à 9 500 DH.",
        "distance": 0.12,
    }
