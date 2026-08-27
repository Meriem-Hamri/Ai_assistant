# 🤖 Documentation — Intégration du pipeline RAG

## 1. Contexte

Le projet **Assistant Intelligent pour documents internes** a pour objectif de permettre à un utilisateur d'interroger une collection de documents en langage naturel.

Le système doit pouvoir retrouver les informations pertinentes dans les documents et générer une réponse basée sur leur contenu.

L'architecture repose sur le principe du **RAG (Retrieval-Augmented Generation)**.

Le RAG combine deux mécanismes :

1. **Retrieval** : recherche des passages pertinents dans les documents.
2. **Generation** : génération d'une réponse à partir des passages récupérés.

L'objectif est de permettre au modèle de langage de répondre en utilisant les informations réellement présentes dans les documents indexés.

---

# 2. Objectif de l'étape RAG

Cette étape avait pour objectif d'intégrer ensemble les composants déjà développés du projet afin de créer un pipeline complet capable de :

```text
Question utilisateur
        ↓
Création de l'embedding
        ↓
Recherche vectorielle
        ↓
Récupération des passages pertinents
        ↓
Construction du contexte
        ↓
Construction du prompt
        ↓
Génération avec le LLM local
        ↓
Réponse + sources
```

Le résultat final est un système capable de recevoir une question et de retourner :

* une réponse générée par le LLM ;
* les sources utilisées pour produire cette réponse.

---

# 3. Architecture générale

Le pipeline RAG repose sur plusieurs composants indépendants :

```text
                    ┌───────────────────┐
                    │ Question utilisateur│
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  RAGPipeline      │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ EmbeddingService  │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   Vector Store    │
                    │    ChromaDB       │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  SearchResult[]   │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  PromptBuilder    │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   Qwen / Ollama   │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   RAGResponse     │
                    └───────────────────┘
```

---

# 4. Le `RAGPipeline`

Le composant principal de cette étape est la classe `RAGPipeline`.

Son rôle est d'orchestrer l'ensemble des composants du système.

Il reçoit :

```text
EmbeddingService
VectorStore
PromptBuilder
LLM
RAGConfig
```

Ces dépendances permettent de conserver une architecture modulaire et testable.

## Responsabilités

Le `RAGPipeline` est responsable de :

1. Valider la question utilisateur.
2. Nettoyer la question.
3. Générer son embedding.
4. Interroger le Vector Store.
5. Récupérer les résultats pertinents.
6. Construire le prompt.
7. Envoyer le prompt au LLM.
8. Construire les sources.
9. Retourner une `RAGResponse`.
10. Traduire les erreurs techniques en erreurs métier du RAG.

---

# 5. Flux d'exécution détaillé

## Étape 1 — Validation de la question

Le pipeline reçoit une question :

```text
"Quelle est la durée du contrat ?"
```

La question est vérifiée afin de s'assurer qu'elle :

* est une chaîne de caractères ;
* n'est pas vide ;
* n'est pas composée uniquement d'espaces.

Les espaces inutiles sont supprimés.

Exemple :

```text
"   Quelle est la durée du contrat ?   "
```

devient :

```text
"Quelle est la durée du contrat ?"
```

---

## Étape 2 — Création de l'embedding

La question est transformée en vecteur numérique grâce à :

```text
EmbeddingService
```

Exemple conceptuel :

```text
"Quelle est la durée du contrat ?"

            ↓

[-0.0900, 0.0005, -0.0497, ...]
```

Cet embedding représente le sens sémantique de la question.

---

# 6. Recherche vectorielle

L'embedding de la question est envoyé au Vector Store.

Le projet utilise :

**ChromaDB**

Le Vector Store recherche les chunks dont les embeddings sont les plus proches de celui de la question.

Exemple :

```text
Question :
Quelle est la durée du contrat ?

Résultats :

1. distance = 0.2764
   Le contrat de travail est conclu
   pour une durée de trois mois.

2. distance = 0.4800
   Le salarié travaille du lundi au vendredi.

3. distance = 0.5271
   Le salaire mensuel est fixé à 8000 dirhams.
```

Plus la distance est faible, plus le résultat est considéré comme proche de la question.

---

# 7. `SearchResult`

Chaque résultat retourné par la recherche vectorielle est représenté par :

```python
@dataclass(slots=True)
class SearchResult:
    chunk_id: str
    text: str
    distance: float
    document_id: str
    document_name: str
    page_number: int
    chunk_index: int
    start_char: int
    end_char: int
```

Ce modèle permet de conserver :

* le contenu du chunk ;
* son identifiant ;
* la distance vectorielle ;
* le document d'origine ;
* la page d'origine ;
* la position du chunk.

---

# 8. Pourquoi `distance` et non `score` ?

Initialement, le projet utilisait un attribut appelé :

```text
score
```

Cependant, ChromaDB retourne directement une **distance**.

Il était donc plus clair et plus précis de renommer :

```text
score
```

en :

```text
distance
```

La différence est importante :

```text
Score élevé  → généralement meilleur résultat
Distance faible → meilleur résultat
```

Comme le système utilise directement la valeur retournée par ChromaDB, le terme `distance` évite toute ambiguïté.

Le flux est donc :

```text
ChromaDB
   ↓
distance
   ↓
SearchResult.distance
   ↓
Source.distance
```

---

# 9. Le paramètre `top_k`

Le paramètre :

```text
top_k
```

détermine le nombre maximum de résultats récupérés.

Exemple :

```python
top_k = 3
```

signifie :

```text
Récupérer au maximum
les 3 chunks les plus proches.
```

Les résultats sont retournés par distance croissante :

```text
distance = 0.27  ← plus pertinent
distance = 0.48
distance = 0.52
```

---

# 10. Le paramètre `max_distance`

Un problème important dans un système RAG est que le Vector Store retourne toujours les résultats les plus proches, même lorsqu'ils ne sont pas réellement pertinents.

Exemple :

```text
Question :
Quelle est la capitale de l'Espagne ?

Documents disponibles :
- contrat de travail
- salaire
- congés
```

ChromaDB peut malgré tout retourner des résultats.

Cependant, ces résultats auront normalement une distance relativement élevée.

Le paramètre :

```python
max_distance
```

permet de filtrer les résultats trop éloignés.

Exemple :

```python
max_distance = 0.5
```

Seuls les résultats tels que :

```text
distance <= 0.5
```

sont conservés.

Cela permet au système d'éviter d'utiliser des documents trop peu pertinents.

---

# 11. Le `PromptBuilder`

Après la recherche vectorielle, les résultats sont transmis au `PromptBuilder`.

Son rôle est de transformer :

```text
Question
+
Chunks récupérés
```

en un prompt compréhensible par le LLM.

Conceptuellement :

```text
CONTEXTE :

[Document : contrat.pdf]
Le contrat de travail est conclu
pour une durée de trois mois.

QUESTION :

Quelle est la durée du contrat ?
```

Le LLM reçoit donc uniquement les informations nécessaires pour répondre.

---

# 12. Le LLM local

Le projet utilise un modèle de langage exécuté localement.

Architecture :

```text
RAGPipeline
     ↓
QwenClient
     ↓
Ollama
     ↓
Qwen
```

L'utilisation d'un modèle local permet :

* de préserver la confidentialité des documents ;
* d'éviter l'envoi de données vers une API externe ;
* de réduire la dépendance à des services cloud ;
* de permettre une utilisation locale.

Le LLM reçoit le prompt construit par le `PromptBuilder` et génère la réponse finale.

---

# 13. `Source`

Chaque source utilisée dans une réponse est représentée par :

```python
@dataclass(frozen=True, slots=True)
class Source:
    document_id: str
    document_name: str
    page_number: int
    chunk_id: str
    distance: float
```

Le modèle est immuable grâce à :

```python
frozen=True
```

Cela garantit que les informations concernant les sources ne sont pas modifiées après la création de la réponse.

---

# 14. `RAGResponse`

La réponse finale du pipeline est représentée par :

```python
@dataclass(frozen=True, slots=True)
class RAGResponse:
    answer: str
    sources: list[Source]
```

Le système retourne donc simultanément :

```text
RAGResponse
│
├── answer
│
└── sources
```

Exemple :

```text
answer:
"La durée du contrat est de trois mois."

sources:
- contrat.pdf
  page : 1
  distance : 0.2764
```

---

# 15. Gestion des erreurs

Le pipeline traduit les erreurs techniques en erreurs spécifiques au domaine RAG.

Les principales erreurs sont :

### `RAGEmbeddingError`

Déclenchée lorsqu'une erreur survient pendant la génération de l'embedding.

```text
Question
   ↓
EmbeddingService
   ❌ erreur
   ↓
RAGEmbeddingError
```

### `RAGRetrievalError`

Déclenchée lorsqu'une erreur survient pendant la recherche vectorielle.

```text
Embedding
   ↓
Vector Store
   ❌ erreur
   ↓
RAGRetrievalError
```

### `RAGGenerationError`

Déclenchée lorsqu'une erreur survient pendant la génération de la réponse.

```text
Prompt
   ↓
LLM
   ❌ erreur
   ↓
RAGGenerationError
```

Cette séparation permet au reste de l'application de comprendre à quelle étape l'erreur s'est produite.

---

# 16. Tests réalisés

## Tests du pipeline

Le pipeline a été testé avec des dépendances simulées :

```text
FakeEmbeddingService
FakeVectorStore
FakePromptBuilder
FakeLLM
```

Les tests ont vérifié notamment :

* le nettoyage de la question ;
* le rejet des questions invalides ;
* la génération de l'embedding ;
* la transmission de `top_k` ;
* la transmission des résultats au Prompt Builder ;
* la transmission du prompt au LLM ;
* le retour de la réponse ;
* la création des sources ;
* le comportement lorsqu'aucun résultat n'est trouvé ;
* la gestion des erreurs.

Résultat :

```text
19 passed
```

---

## Tests du ChromaStore

Les tests du Vector Store ont validé :

* l'initialisation ;
* l'ajout des chunks ;
* la recherche ;
* la suppression d'un document ;
* le nettoyage de la collection ;
* la recherche dans une collection vide ;
* la validation des embeddings ;
* la validation de `top_k` ;
* le retour des distances ;
* le filtrage avec `max_distance`.

Résultat final :

```text
18 tests validés
```

---

# 17. Test des distances

Un test spécifique a été réalisé pour observer le comportement réel des distances retournées par ChromaDB.

Exemple :

```text
QUESTION :
Quelle est la durée du contrat ?

1. distance = 0.2764
   Le contrat de travail est conclu pour une durée de trois mois.

2. distance = 0.4800
   Le salarié travaille du lundi au vendredi.

3. distance = 0.5271
   Le salaire mensuel est fixé à 8000 dirhams.
```

Le résultat pertinent possède bien la distance la plus faible.

Une question sans rapport avec les documents a également produit des distances plus élevées.

Cette observation a permis de préparer l'utilisation du paramètre :

```text
max_distance
```

pour filtrer les résultats insuffisamment pertinents.

---

# 18. Test End-to-End réel

Un test End-to-End réel a été réalisé avec les composants réels du projet.

Le pipeline testé était :

```text
EmbeddingService réel
        ↓
ChromaStore réel
        ↓
ChromaDB réel
        ↓
PromptBuilder réel
        ↓
QwenClient réel
        ↓
Ollama
        ↓
Qwen
```

Question :

```text
Quelle est la durée du contrat ?
```

Résultat obtenu :

```text
RÉPONSE :

La durée du contrat est de trois mois.
```

Sources :

```text
- contrat.pdf | page=1 | distance=0.2764
- contrat.pdf | page=2 | distance=0.4800
- contrat.pdf | page=3 | distance=0.5271
```

Résultat du test :

```text
1 passed
```

Ce test valide le fonctionnement réel de l'intégration RAG.

---

# 19. Résultat final de l'étape

À la fin de cette étape, le système RAG est capable de :

```text
Question utilisateur
        ↓
Validation
        ↓
Embedding local
        ↓
Recherche vectorielle locale
        ↓
Filtrage des résultats
        ↓
Construction du contexte
        ↓
Construction du prompt
        ↓
Génération avec Qwen local
        ↓
Réponse finale
        +
Sources documentaires
```

L'ensemble fonctionne localement, sans API externe pour la chaîne RAG.

---

# 20. État actuel du projet

| Étape                          | État |
| ------------------------------ | ---- |
| Extraction                     | ✅    |
| Cleaning                       | ✅    |
| Chunking                       | ✅    |
| Embeddings                     | ✅    |
| Vector Store                   | ✅    |
| ChromaDB                       | ✅    |
| Recherche vectorielle          | ✅    |
| Prompt Builder                 | ✅    |
| LLM local                      | ✅    |
| Intégration RAG                | ✅    |
| Tests unitaires                | ✅    |
| Tests d'intégration            | ✅    |
| Tests End-to-End               | ✅    |
| Documentation RAG              | ✅    |
| Validation sur vrais documents | ⏳    |
| Interface utilisateur          | ⏳    |

---

# 21. Prochaine étape

La prochaine étape recommandée est la **validation complète sur de vrais documents**.

Le test E2E actuel valide très bien :

```text
Chunk → Embedding → ChromaDB → RAG
```

Mais l'application réelle doit fonctionner avec :

```text
PDF / DOCX / Image
       ↓
Extraction
       ↓
OCR si nécessaire
       ↓
Cleaning
       ↓
Chunking
       ↓
Embeddings
       ↓
ChromaDB
       ↓
RAG
       ↓
Réponse + sources
```

La prochaine phase devra donc tester au minimum :

1. **Un PDF contenant du texte natif** ;
2. **Un PDF scanné nécessitant l'OCR** ;
3. **Un document Word (`.docx`)** ;
4. **Une image contenant du texte**.

---

## Conclusion

**L'étape d'intégration RAG peut être considérée comme terminée et validée.** ✅

Le cœur fonctionnel de l'Assistant IA est maintenant en place. La prochaine étape est une validation réaliste de la chaîne complète avec différents types de documents, avant de commencer l'interface utilisateur.

