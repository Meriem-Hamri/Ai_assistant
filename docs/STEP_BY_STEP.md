# STEP-BY-STEP — Guide d'utilisation, tests et dépannage

Ce document décrit, pas à pas, comment préparer l'environnement, exécuter la suite de tests, quelles modifications ont été apportées au dépôt (tests/), et des solutions de contournement pour les dépendances lourdes. Le contenu est en français.

## Objectif
- Fournir des instructions reproductibles pour installer les dépendances et lancer les tests.
- Décrire les changements récents faits pour améliorer les tests (fixture pytest session-scoped).
- Donner des conseils de dépannage pour les problèmes les plus probables.

---

## Prérequis
- Python 3.10+ (la machine utilisée pour le développement utilise Python 3.14 dans les exemples de commandes).
- Accès réseau pour installer des paquets PyPI (sauf si vous utilisez un mirror local).
- Recommandé : créer un environnement virtuel `venv` pour isoler les dépendances.

### Créer et activer un venv (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Créer et activer un venv (Windows cmd)
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

---

## Installation des dépendances de base
1. Mettre pip à jour :
```powershell
python -m pip install --upgrade pip
```

2. Installer les dépendances minimales nécessaires pour exécuter les tests unitaires rapides :
```powershell
python -m pip install pytest numpy
```

3. Dépendances optionnelles (lourdes) pour la partie embeddings local (ex: sentence-transformers, PyTorch) :
```powershell
python -m pip install "sentence-transformers"
# Note: sentence-transformers peut tirer PyTorch et autres dépendances lourdes.
```

Si vous préférez éviter d'installer ces paquets lourds localement (par exemple pour une CI légère), voir la section "Alternative : mocker EmbeddingService" plus bas.

---

## Exécuter les tests
- Commande recommandée (utiliser `python -m pytest` pour éviter les problèmes de PATH) :
```powershell
python -m pytest -q
```

- Si `pytest` est installé mais pas dans le PATH, `python -m pytest` fonctionne toujours.

---

## Modifications apportées au dépôt (tests)
Pour réduire le temps d'initialisation des tests et éviter de recréer plusieurs fois l'instance d'embedding, une fixture pytest session-scoped a été ajoutée et les tests existants ont été modifiés pour l'utiliser.

Fichiers modifiés/ajoutés :
- `tests/conftest.py` (nouveau) : contient la fixture `embedding_service` avec `scope="session"`.
  - Contenu :
    ```python
    import pytest
    from app.embeddings.embedding_service import EmbeddingService

    @pytest.fixture(scope="session")
    def embedding_service():
        """Session-scoped EmbeddingService instance reused by all tests."""
        return EmbeddingService()
    ```
- `tests/test_embeddings.py` : remplacements des instanciations `service = EmbeddingService()` par `service = embedding_service` afin d'utiliser la fixture unique.

Pourquoi ?
- Créer une instance d'`EmbeddingService` peut être coûteux (chargement d'un modèle, initialisation de ressources). Une fixture `scope='session'` crée l'objet une seule fois pour toute la session de tests, ce qui accélère significativement l'exécution.

---

## Alternatives et bonnes pratiques
### 1) Mocker EmbeddingService pour tests unitaires rapides
Si l'installation de `sentence-transformers` / PyTorch est trop lourde ou impossible dans l'environnement CI, il est recommandé de remplacer la dépendance réelle par un mock dans les tests :
- Utiliser `unittest.mock` / `pytest-mock` pour rendre les méthodes `embed` / `embed_batch` déterministes et rapides.

Exemple minimal :
```python
# dans un test ou fixture
from unittest.mock import MagicMock

embedding_service.embed = MagicMock(return_value=np.zeros(embedding_service.dimension))
embedding_service.embed_batch = MagicMock(return_value=np.zeros((3, embedding_service.dimension)))
```

Cela permet d'exécuter toute la logique de tests autour des utilitaires (normalize_vector, cosine_similarity, pipeline) sans charger de poids ML.

### 2) Tests d'intégration (optionnels)
- Conserver deux catégories de tests : unitaires (rapides, mockés) et intégration (vraies dépendances). CI peut exécuter seulement les tests unitaires en PRs et lancer les tests d'intégration en nightly.

---

## Dépannage (FAQ)

Q : `pytest` ou `python -m pytest` renvoie une erreur "No module named 'numpy'" ou autre ModuleNotFoundError ?
- Solution : installer la dépendance manquante via pip (ex: `python -m pip install numpy`). Assurez-vous d'activer le venv si vous en utilisez un.

Q : `pytest` n'est pas reconnu (commande introuvable) alors que pytest est installé pour l'utilisateur ?
- Cause fréquente : scripts installés dans `C:\Users\<user>\AppData\Roaming\Python\Python3X\Scripts` ne sont pas dans le PATH.
- Solution : utilisez `python -m pytest` ou ajoutez le dossier Scripts à la variable PATH.

Q : L'installation de `sentence-transformers` échoue ou semble bloquer (Windows, CUDA, compatibilité) ?
- Solution :
  - Vérifier la compatibilité PyTorch/CUDA pour votre machine.
  - Installer une version CPU-only de PyTorch si GPU non disponible : suivez les instructions officielles de PyTorch (https://pytorch.org/get-started/locally/).
  - Si impossible, utiliser la méthode de mocking décrite ci‑dessus pour les tests unitaires.

---

## Commandes récapitulatives utiles
- Mettre à jour pip et installer pytest + numpy :
```powershell
python -m pip install --upgrade pip
python -m pip install pytest numpy
python -m pytest -q
```

- Installer sentence-transformers (optionnel / lourd) :
```powershell
python -m pip install "sentence-transformers"
```

- Exécuter un test spécifique :
```powershell
python -m pytest tests/test_embeddings.py::test_embedding_dimension -q
```

---

## Notes finales
- La fixture `embedding_service` améliore la performance des tests en réutilisant une seule instance d'`EmbeddingService` pour toute la session de tests.
- Pour les environnements contraints, privilégier le mocking afin de garder la suite de tests rapide et fiable.

Si vous le souhaitez, je peux :
- ajouter un exemple de fixture mockée dans `tests/conftest.py` (optionnel),
- générer un `requirements-dev.txt` listant `pytest`, `numpy`, et les dépendances de test,
- ou créer une Git commit contenant ces nouveaux fichiers et modifications.
