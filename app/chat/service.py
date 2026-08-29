from app.rag.pipeline import RAGPipeline
from app.api.schemas.chat import ChatResponse, ChatSourceResponse


class ChatService:
    """
    Service responsable du traitement des questions utilisateur
    via le pipeline RAG.
    """

    def __init__(self, rag_pipeline: RAGPipeline) -> None:
        self._rag_pipeline = rag_pipeline

    def send_message(
        self,
        question: str,
        document_id: str | None = None,
    ) -> ChatResponse:

        response = self._rag_pipeline.answer(
            question=question,
            document_id=document_id,
        )

        sources = [
            ChatSourceResponse(
                document_id=source.document_id,
                document_name=source.document_name,
                page_number=source.page_number,
                distance=source.distance,
            )
            for source in response.sources
        ]

        return ChatResponse(
            answer=response.answer,
            sources=sources,
        )