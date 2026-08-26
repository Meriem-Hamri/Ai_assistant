class RAGError(Exception):
    """
    Exception de base pour les erreurs du pipeline RAG.
    """


class RAGEmbeddingError(RAGError):
    """
    Erreur lors de la génération de l'embedding de la question.
    """


class RAGRetrievalError(RAGError):
    """
    Erreur lors de la recherche vectorielle.
    """


class RAGGenerationError(RAGError):
    """
    Erreur lors de la génération de la réponse par le LLM.
    """