import numpy as np

from app.embeddings.embedding_service import EmbeddingService
from app.embeddings.utils import (
    normalize_vector,
    cosine_similarity,
)


def test_embedding_service_initialization(embedding_service):
    """
    Vérifie que le service d'embedding est correctement initialisé.
    """

    assert embedding_service.model is not None


def test_embedding_dimension(embedding_service):
    """
    Vérifie que le modèle expose une dimension valide.
    """

    assert isinstance(embedding_service.dimension, int)
    assert embedding_service.dimension > 0


def test_embed_returns_numpy_array(embedding_service):
    """
    Vérifie qu'un embedding est un tableau NumPy.
    """

    embedding = embedding_service.embed("Bonjour tout le monde.")

    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (embedding_service.dimension,)


def test_embed_batch(embedding_service):
    """
    Vérifie que plusieurs textes sont correctement encodés.
    """

    texts = [
        "Bonjour",
        "Bonsoir",
        "Bonne nuit",
    ]

    embeddings = embedding_service.embed_batch(texts)

    assert isinstance(embeddings, np.ndarray)

    assert embeddings.shape == (
        len(texts),
        embedding_service.dimension,
    )


def test_normalize_vector():
    """
    Vérifie qu'un vecteur est correctement normalisé.
    """

    vector = np.array([3.0, 4.0])

    normalized = normalize_vector(vector)

    assert np.isclose(
        np.linalg.norm(normalized),
        1.0,
    )


def test_cosine_similarity_identical_vectors():
    """
    Deux vecteurs identiques doivent avoir
    une similarité cosinus égale à 1.
    """

    vector1 = np.array([1.0, 0.0])

    vector2 = np.array([1.0, 0.0])

    similarity = cosine_similarity(
        vector1,
        vector2,
    )

    assert np.isclose(similarity, 1.0)


def test_cosine_similarity_orthogonal_vectors():
    """
    Deux vecteurs orthogonaux doivent avoir
    une similarité proche de 0.
    """

    vector1 = np.array([1.0, 0.0])

    vector2 = np.array([0.0, 1.0])

    similarity = cosine_similarity(
        vector1,
        vector2,
    )

    assert np.isclose(similarity, 0.0)


def test_semantically_similar_sentences():
    """
    Deux phrases parlant du même sujet doivent
    être plus proches qu'une phrase sans rapport.
    """

    service = EmbeddingService()

    sentence1 = "Le chat dort sur le canapé."

    sentence2 = "Le félin est allongé sur le sofa."

    sentence3 = "La voiture roule sur l'autoroute."

    embedding1 = service.embed(sentence1)

    embedding2 = service.embed(sentence2)

    embedding3 = service.embed(sentence3)

    similarity_close = cosine_similarity(
        embedding1,
        embedding2,
    )

    similarity_far = cosine_similarity(
        embedding1,
        embedding3,
    )

    assert similarity_close > similarity_far