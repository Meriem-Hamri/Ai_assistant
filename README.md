# 🤖 Assistant AI - Recherche Documentaire & RAG 100% Local

## Quick Start
Pour une procédure détaillée pas à pas (installation, exécution des tests, dépannage), voir : `docs/STEP_BY_STEP.md`.

Ce projet est une solution de recherche documentaire intelligente exploitant des modèles d'Intelligence Artificielle (IA) locaux. L'objectif principal est de concevoir un système capable d'importer des documents multi-formats (PDF, Word, Images), d'en extraire le contenu textuel (avec OCR si nécessaire), de l'indexer de manière sémantique, et de répondre aux questions des utilisateurs de façon contextualisée et 100% locale (sans connexion internet ni cloud).

---

## 🗺️ Roadmap & État d'avancement des Étapes

L'architecture finale s'articule autour de 7 étapes clés :

### Étape 1 : Client LLM Local ↔ Ollama 
* **Statut** : **Terminé** ✅
* **Description** : Mise en place de l'orchestration du modèle local `qwen3:4b` (ou Qwen 2.5) via Ollama pour répondre aux questions.

### Étape 2 : Extraction et Détection Automatique 
* **Statut** : **En cours (Finalisation)** 🔄
* **Description** : Lecture des PDF (textuels), fichiers Word (DOCX) et détection automatique du format. Initialisation de la brique OCR (PaddleOCR) pour les fichiers scannés et les images.

### Étape 3 : Nettoyage du texte 
* **Statut** : **Implémenté** ✅
* **Description** : Suppression du bruit (caractères spéciaux, sauts de ligne inutiles, espaces superflus, caractères de contrôle) pour obtenir un texte propre avant l'indexation. Le nettoyage s'applique directement aux `DocumentPage` du `Document` sans créer un nouveau document.

#### Détail de l'étape 3
La phase de cleaning intervient juste après l'extraction. À ce stade, le texte peut être bruité à cause de plusieurs facteurs :
- retours à la ligne mal gérés,
- espaces ou tabulations répétitifs,
- caractères invisibles ou non imprimables,
- lignes vides inutiles,
- sauts de paragraphes incohérents.

L'objectif est de transformer ce texte brut en un texte structuré, lisible et prêt à être utilisé par les étapes suivantes (chunking, embeddings, recherche sémantique).

Le nettoyage est réalisé par `app/cleaning/cleaner.py` à travers plusieurs fonctions :
- `normalize_line_breaks()` : normalise les retours à la ligne,
- `remove_control_characters()` : supprime les caractères de contrôle,
- `normalize_spaces()` : réduit les espaces répétitifs,
- `remove_empty_lines()` : enlève les lignes vides parasites,
- `strip_text()` : enlève les espaces en début et fin de texte.

La fonction `clean_document()` applique ces transformations directement sur le contenu de chaque page du document et ajoute des métadonnées indiquant que le nettoyage a été effectué.

### Étape 4 : Découpage sémantique (Chunking) 
* **Statut** : **Planifié** ⏳
* **Description** : Découpage des textes volumineux en blocs (chunks) de taille homogène avec chevauchement (overlap) pour conserver le contexte.

### Étape 5 : Embeddings (Vectorisation) 
* **Statut** : **Planifié** ⏳
* **Description** : Transformation de chaque bloc de texte en vecteur numérique représentant son sens sémantique.

### Étape 6 : Base de données vectorielle (ChromaDB) 
* **Statut** : **Planifié** ⏳
* **Description** : Stockage persistant local des embeddings et recherche rapide par similarité cosinus.

### Étape 7 : Pipeline de requêtage RAG 
* **Statut** : **Planifié** ⏳
* **Description** : Intégration de la question utilisateur -> Recherche des blocs pertinents -> Envoi du contexte au LLM -> Génération de la réponse finale avec citation des sources.

---

## 🏗️ Architecture Détaillée du Système

> Pour une documentation d'architecture plus détaillée, voir [ARCHITECTURE.md](ARCHITECTURE.md).


### Diagramme de flux d'ingestion (Indexation)
```mermaid
graph TD
    A[Document: PDF, DOCX, Image] --> B[detector.py]
    B -->|PDF textuel| C[pdf_reader.py]
    B -->|DOCX| D[docx_reader.py]
    B -->|Scan/Image| E[ocr_reader.py]
    C --> F[Document / DocumentPage]
    D --> F
    E --> F
    F --> G[cleaner.py - Nettoyage]
    G --> H[Chunking - Découpage]
    H --> I[Embeddings - Vectorisation]
    I --> J[ChromaDB - Base Vectorielle]
```

### Diagramme de flux de requêtage (Query Pipeline)
```mermaid
graph TD
    K[Question utilisateur] --> L[Génération Embedding Question]
    L --> M[Recherche de similarité dans ChromaDB]
    M -->|Top K passages les plus pertinents| N[Formulation du Prompt Contextuel]
    N --> O[qwen_client.py via Ollama]
    O --> P[Réponse finale + Sources documentaires]
```

---

## 🧼 Étape 3 : Nettoyage du texte (Cleaning)

Dans un système RAG (Retrieval-Augmented Generation) local, le nettoyage du texte après l'extraction brute est une étape critique. Les documents extraits (PDF, Word, Scans OCR) contiennent souvent beaucoup de bruit textuel qui peut dégrader la qualité des embeddings et perturber le modèle de langage.

### 1. Pourquoi le nettoyage est-il crucial ?
* **Préservation du sens sémantique** : Les mots coupés en fin de ligne (ex. `infor-` et `mation`), les en-têtes et pieds de page répétés à chaque page ajoutent un bruit inutile que le modèle vectoriel peut mal interpréter.
* **Optimisation de la fenêtre de contexte** : Envoyer des espaces superflus, des sauts de page inutiles ou du texte répétitif au LLM consomme des jetons (tokens) inutilement et ralentit la génération locale.
* **Amélioration de la similarité sémantique** : Un texte propre garantit que la recherche de similarité s'effectue sur le contenu informatif réel et non sur des artefacts de mise en page.

### 2. Opérations clés du nettoyage
Le module `app/cleaning/cleaner.py` aura pour rôle d'appliquer les transformations suivantes :
* **Normalisation des espaces et sauts de ligne** : Remplacement des espaces multiples, tabulations et retours à la ligne consécutifs par des espaces uniques ou des sauts de paragraphe propres.
* **Reconstruction des mots coupés (Hyphenation)** : Détection et fusion des mots coupés en fin de ligne par un trait d'union (ex. `déve-\nloppement` devient `développement`).
* **Suppression des en-têtes et pieds de page (Headers & Footers)** : Identification et suppression des textes récurrents en haut ou en bas de chaque page (ex. titre du document, numérotation comme `Page 3 sur 10`).
* **Nettoyage des artefacts d'OCR** : Suppression des caractères parasites fréquents dans les documents scannés (ex. caractères isolés comme `~`, `|`, `_`, ou suites incohérentes de signes de ponctuation).
* **Normalisation de l'encodage** : Conversion des caractères spéciaux et correction des erreurs d'encodage (ex. mauvaise conversion UTF-8 / Windows-1252 créant des caractères corrompus comme `Ã©` au lieu de `é`).

### 3. Structure d'implémentation proposée
Le fichier `app/cleaning/cleaner.py` contiendra :
* Des fonctions utilitaires dédiées à chaque type de nettoyage (ex: `remove_extra_whitespace(text: str)`, `fix_hyphenation(text: str)`, `remove_headers_footers(text: str)`).
* Une fonction principale `clean_document(document: Document) -> Document` qui applique ces règles séquentiellement sur le texte de chaque `DocumentPage` présente dans l'objet `Document` avant l'étape de découpage (chunking).

---

## 📄 Documentation Fichier par Fichier

Voici la description précise du rôle de chaque fichier actuellement présent dans l'espace de travail :

### 1. Dossier Racine

*   **[main.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/main.py)**  
    *   **Description** : Point d'entrée de l'application. Utilisé pour tester rapidement l'extraction en affichant le contenu extrait d'un fichier PDF de démonstration.
*   **[requirements.txt](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/requirements.txt)**  
    *   **Description** : Fichier contenant les dépendances Python requises pour le projet (ex. `pymupdf`, `python-docx`, `paddleocr`, `ollama`, `chromadb`, etc.).

### 2. Modèles de données (`app/models/`)

*   **[app/models/document.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/app/models/document.py)**  
    *   **Description** : Contient les structures de données en `dataclass` qui circulent à travers le pipeline.
    *   **Classes majeures** :
        *   `DocumentPage` : Représente une page avec son `page_number` (int) et son `text` (str).
        *   `Document` : Structure racine représentant un fichier entier, contenant un `filename` (nom du fichier), un `id` unique (UUID4), une liste de `DocumentPage`, et un dictionnaire de `metadata` (ex: type de fichier, nombre de pages).
        *   `Chunk` : Prévu pour les étapes futures afin de stocker les fragments de texte avec leur source.

### 3. Module d'Extraction (`app/extraction/`)

*   **[app/extraction/pdf_reader.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/app/extraction/pdf_reader.py)**  
    *   **Description** : Module d'extraction de texte pour les PDF textuels.
    *   **Technologie** : `PyMuPDF` (importé via `fitz`).
    *   **Fonction** : `extract_text_from_pdf(filePath: str) -> Document`. Parcourt chaque page du document PDF, extrait le texte brut nettoyé des espaces superflus, et remplit l'objet `Document`.
*   **[app/extraction/docx_reader.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/app/extraction/docx_reader.py)**  
    *   **Description** : Module d'extraction de texte pour les documents Word `.docx`.
    *   **Technologie** : `python-docx`.
    *   **Fonction** : `extract_text_from_docx(file_path: str) -> Document`. Parcourt l'ensemble des paragraphes non vides du document, les regroupe dans une seule page logique (`page_number=1`), et renvoie l'objet `Document`.
*   **[app/extraction/ocr_reader.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/app/extraction/ocr_reader.py)**  
    *   **Description** : Module de reconnaissance optique de caractères (OCR) pour les documents scannés ou images.
    *   **Technologie** : `PaddleOCR` (configuré pour la langue française `lang="fr"`).
    *   **État** : L'instance `ocr` est initialisée. La fonction finale d'extraction reste à implémenter.
*   **[app/extraction/detector.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/app/extraction/detector.py)**  
    *   **Description** : Routeur intelligent du module d'extraction.
    *   **Fonction** : `load_document(file_path: str) -> Document`. Analyse l'extension du fichier en minuscule (ex. `.pdf`, `.docx`) et redirige automatiquement l'appel vers la bonne fonction d'extraction (`extract_text_from_pdf` ou `extract_text_from_docx`).
*   **[app/extraction/extraction_service.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/app/extraction/extraction_service.py)**  
    *   **Description** : Squelette vide destiné à orchestrer plus tard les services d'extraction à un plus haut niveau (par exemple pour l'API FastAPI).

### 4. Module LLM (`app/llm/`)

*   **[app/llm/qwen_client.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/app/llm/qwen_client.py)**  
    *   **Description** : Client de connexion locale pour interagir avec le modèle d'IA de génération.
    *   **Technologie** : `ollama`.
    *   **Fonction** : `ask_qwen(question: str) -> str`. Envoie une invite au modèle local `qwen3:4b` et retourne sa réponse textuelle sous forme de chaîne de caractères.

### 5. Module de Nettoyage (`app/cleaning/`)

*   **[app/cleaning/cleaner.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/app/cleaning/cleaner.py)**  
    *   **Description** : Fichier vide (squelette) destiné à héberger les règles de nettoyage linguistique et textuel lors de l'Étape 3.

### 6. Suite de Tests (`tests/`)

*   **[tests/test_paddle.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/tests/test_paddle.py)** : Vérifie le bon chargement de la bibliothèque `paddle`, sa version et la détection CUDA ou CPU.
*   **[tests/test_ocr.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/tests/test_ocr.py)** : Effectue une prédiction brute de texte avec `PaddleOCR` sur l'image de test `documents/images/images.jpg` pour valider le fonctionnement de la brique de reconnaissance.
*   **[tests/test_pdf.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/tests/test_pdf.py)** : Teste l'extraction d'un fichier PDF volumineux (`50_pages.pdf`). *Note : Fait actuellement référence à un nom de fonction temporaire `extract_pdf_text`.*
*   **[tests/test_docx.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/tests/test_docx.py)** : Valide l'extraction de texte sur le fichier Word `HAMRI_MERIEM_Demande_de_Stage.docx` et affiche la sortie structurée.
*   **[tests/test_detector.py](file:///C:/Users/merie_luskpw8/Documents/AssistantAI/tests/test_detector.py)** : Valide le chargement via `load_document` sur le fichier `final.pdf` et vérifie la structure de données renvoyée.

---

## 🛠️ Comment Exécuter les Tests

Pour s'assurer du bon fonctionnement de chaque composant, vous pouvez exécuter individuellement les scripts de tests à la racine du projet :

```bash
# Pour tester la détection matérielle de Paddle
python tests/test_paddle.py

# Pour tester l'OCR de Paddle OCR sur une image
python tests/test_ocr.py

# Pour tester l'extraction d'un fichier DOCX
python tests/test_docx.py

# Pour tester le détecteur automatique
python tests/test_detector.py
```