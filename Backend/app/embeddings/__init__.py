import numpy as np

"""
Fonctions utilitaires pour la manipulation des embeddings.

Ce module contient uniquement des opérations mathématiques
indépendantes du modèle utilisé.
"""

def normalize_vector(vector: np.ndarray) ->np.ndarray:
    """
    Normalise un vecteur.

    Args:
        vector: vecteur numpy.

    Returns:
        Le vecteur normalisé.
    """

    norm = np.linalg.norm(vector)

    if norm == 0:
        return vector

    return vector / norm

def cosine_similarity(
    vector1: np.ndarray,
    vector2: np.ndarray,
) -> float:
    """
    Calcule la similarité cosinus entre deux vecteurs.

    Args:
        vector1: premier vecteur.
        vector2: second vecteur.

    Returns:
        Similarité cosinus.
    """

    vector1 = normalize_vector(vector1)
    vector2 = normalize_vector(vector2)

    return float(np.dot(vector1, vector2))

# def pairwise_similarity(
#     embeddings: np.ndarray,
# ) -> np.ndarray:
#     """
#     Calcule la matrice de similarité cosinus entre plusieurs embeddings.

#     Args:
#         embeddings: matrice (n_embeddings, dimension).

#     Returns:
#         Matrice carrée de similarité.
#     """

#     normalized = np.array(
#         [normalize_vector(v) for v in embeddings]
#     )

#     return normalized @ normalized.T