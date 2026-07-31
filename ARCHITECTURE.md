# Architecture et documentation du projet Assistant AI

## 1. Objectif du projet
Ce projet vise à créer une solution de recherche documentaire locale capable d'ingérer et d'extraire du texte depuis des documents multi-formats : PDF textuels, documents Word (.docx), images et documents scannés. L'objectif final est de pouvoir utiliser ces contenus comme base pour un système de question/réponse assisté par un modèle local (RAG / retrieval-augmented generation).

## 2. Vue d'ensemble de l'architecture

### 2.1 Flux principal
1. Le document arrive dans le système.
2. `detector.py` identifie le format du fichier et redirige le traitement vers le bon lecteur.
3. Chaque lecteur transforme le fichier en un objet `Document` structuré avec des pages et du texte.
4. Le texte extrait peut ensuite être nettoyé, découpé en fragments, converti en embeddings et indexé dans une base vectorielle.
5. Les questions utilisateur sont envoyées à un modèle local via `qwen_client.py`.

### 2.2 Modules principaux
- `app/models/document.py` : structure des données documentaires.
- `app/extraction/` : extraction de contenu depuis différents formats.
- `app/llm/qwen_client.py` : interface vers le modèle de génération locale.
- `app/cleaning/cleaner.py` : emplacement prévu pour les traitements de nettoyage.
- `tests/` : validations de bout en bout des principaux composants.

## 3. Fichier par fichier

### 3.1 Fichiers racine
- `main.py`
  - Point d'entrée minimal du projet.
  - Appelle aujourd'hui `extract_pdf_text` sur un fichier de démonstration et affiche le résultat.
  - Sert principalement de preuve de concept pour l'extraction PDF.

- `requirements.txt`
  - Fichier de dépendances Python.
  - Actuellement vide dans le dépôt, mais il doit contenir toutes les bibliothèques requises comme `pymupdf`, `python-docx`, `paddleocr`, `ollama`, etc.

### 3.2 Modèles de données
- `app/models/document.py`
  - Définit `DocumentPage`, `Document`, et `Chunk`.
  - `DocumentPage` contient un numéro de page et le texte extrait.
  - `Document` contient le nom du fichier, un identifiant unique UUID, une liste de pages et un dictionnaire `metadata`.
  - `Chunk` est prévu pour la future étape de découpage sémantique et d'indexation.

### 3.3 Extraction de documents
- `app/extraction/pdf_reader.py`
  - Lit un fichier PDF avec `PyMuPDF` (`fitz`).
  - Pour chaque page, extrait le texte brut via `page.get_text()`.
  - Crée un objet `Document` avec un `DocumentPage` par page.
  - Ajoute des métadonnées : type de document et nombre de pages.
  - Gère les erreurs de fichier manquant et renvoie des `ValueError` pour les problèmes de lecture.

- `app/extraction/docx_reader.py`
  - Lit un fichier Word `.docx` avec `python-docx`.
  - Concatène tous les paragraphes non vides en une seule page logique.
  - Crée un objet `Document` avec `page_number=1` et ajoute le type `docx` dans les métadonnées.
  - Gère les erreurs d'accès ou de lecture.

- `app/extraction/ocr_reader.py`
  - Configure une instance `PaddleOCR` pour le français.
  - Dans l'état actuel, le fichier initialise uniquement l'instance OCR.
  - Les options sont explicitement configurées pour désactiver l'orientation du document, le redressement et l'orientation de ligne.
  - Ce fichier est utile pour centraliser la configuration OCR, mais n'exporte pas encore de fonction d'extraction.

- `app/extraction/image_reader.py`
  - Configure une seconde instance `PaddleOCR` pour le français (avec paramètres par défaut).
  - Définit `extract_text_from_image(file_path: str) -> Document`.
  - Vérifie l'existence du fichier image.
  - Exécute `ocr.predict()` sur l'image et extrait les textes recònvus depuis `result["rec_texts"]`.
  - Recompile le texte en une chaîne unique et le place dans une seule page de `Document`.
  - Cette fonction est la brique opérationnelle OCR actuelle pour les images.

- `app/extraction/detector.py`
  - Détecte le format du document à partir de l'extension de fichier.
  - Prend en charge `.pdf` et `.docx` aujourd'hui.
  - Redirige vers `extract_text_from_pdf` ou `extract_text_from_docx`.
  - Si le format n'est pas supporté, lance une `ValueError`.
  - Note : le routeur ne prend pas encore en charge les images/OCR (`.jpg`, `.png`) ni les PDF scannés.

- `app/extraction/extraction_service.py`
  - Fichier actuellement vide.
  - Sert de squelette pour la future orchestration d'un service d'extraction plus large (API, orchestration multi-format, traitement asynchrone, etc.).

### 3.4 Module LLM
- `app/llm/qwen_client.py`
  - Interface minimale vers le modèle local via `ollama.chat`.
  - La fonction `ask_qwen(question: str) -> str` envoie une demande au modèle `qwen3:4b`.
  - Retourne le texte de réponse du modèle.
  - Ce module est prêt à être utilisé pour la partie génération de réponses dans un pipeline RAG.

### 3.5 Nettoyage
- `app/cleaning/cleaner.py`
  - Module chargé de transformer le texte brut issu de l'extraction en un texte propre, lisible et homogène.
  - Son rôle est de corriger les imperfections structurelles du texte sans changer la logique du document : les modifications portent sur les `DocumentPage` du document existant, et non sur la création d'un nouveau `Document`.
  - Le nettoyage intervient après l'extraction et avant les étapes suivantes du pipeline (chunking, embeddings, recherche sémantique).
  - Les transformations effectuées sont les suivantes :
    - normalisation des retours à la ligne (`\n`, `\r\n`, `\f`),
    - suppression des caractères de contrôle invisibles,
    - réduction des espaces et tabulations multiples,
    - suppression des lignes vides inutiles,
    - retrait des espaces en début et fin de texte.
  - La fonction `clean_text()` applique l'ensemble de ces règles sur une chaîne de caractères.
  - La fonction `clean_document()` applique ce nettoyage à toutes les pages du document et ajoute des métadonnées pour signaler que le document a été nettoyé.
  - Ce module est volontairement simple à ce stade : il se concentre sur la qualité structurelle du texte. Les règles plus avancées (suppression de signatures, en-têtes répétitifs, formats spécifiques, etc.) pourront être ajoutées plus tard si nécessaire.
  - Les tests associés sont présents dans `tests/test_etape3.py` et couvrent les cas PDF, DOCX et image (OCR).

### 3.6 Tests existants
- `tests/test_paddle.py`
  - Vérifie le chargement de Paddle et ses informations d'environnement (`version`, compilation CUDA, device utilisé).

- `tests/test_ocr.py`
  - Instancie `PaddleOCR` avec la configuration du fichier `ocr_reader.py`.
  - Exécute la prédiction sur `documents/images/images.jpg`.
  - Affiche le résultat pour vérifier que l'OCR fonctionne.

- `tests/test_image.py`
  - Appelle `extract_text_from_image` sur une image de test.
  - Affiche le nom de fichier et le texte extrait.

- `tests/test_docx.py`
  - Appelle `extract_text_from_docx` sur un fichier Word de test.
  - Affiche la sortie structurée page par page.

- `tests/test_pdf.py`
  - Appelle `extract_pdf_text` sur un fichier PDF de test.
  - Affiche le texte page par page.

- `tests/test_detector.py`
  - Appelle `load_document` pour un PDF et affiche le nom du document et les numéros de pages.

## 4. Ce qui a été réalisé jusqu'à présent

### Étapes déjà implémentées
- Implémentation d'un modèle de données documentaires clair et extensible (`Document`, `DocumentPage`, `Chunk`).
- Extraction de texte pour les fichiers PDF textuels avec `PyMuPDF`.
- Extraction de texte pour les fichiers Word `.docx` avec `python-docx`.
- Configuration initiale de PaddleOCR pour le français.
- Mise en place d'un routeur de format `detector.py` permettant de choisir le lecteur approprié.
- Mise en place d'un client local pour modèle LLM via `ollama`.
- Développement de tests d'intégration simples permettant de valider chaque type d'extraction.

### Points d'attention
- L'intégration OCR est partielle : la seule fonction d'extraction OCR opérationnelle se trouve dans `image_reader.py`, tandis que `ocr_reader.py` reste essentiellement de la configuration.
- Le routeur `load_document` ne gère actuellement pas les formats images / scannés.
- Le nettoyage de texte est maintenant implémenté via `app/cleaning/cleaner.py` et modifie les pages du `Document` en place.
- Le découpage sémantique et la vectorisation ne sont pas encore présents.
- La base de données vectorielle n'est pas encore en place.

## 5. Prochaines étapes recommandées

1. **Compléter l'intégration OCR**
   - Ajouter `extract_text_from_image` ou une fonction équivalente dans `ocr_reader.py`.
   - Faire en sorte que `detector.py` prenne en charge les images et les PDF scannés.

2. **Créer le service d'extraction**
   - Utiliser `extraction_service.py` pour exposer un point d'entrée unique, par exemple une API ou une fonction `ingest_document`.

3. **Nettoyage de texte**
   - Le nettoyage est maintenant en place ; il reste à l'intégrer plus largement dans l'orchestre du pipeline si nécessaire.

4. **Chunking et embeddings**
   - Ajouter la génération de fragments de texte (`Chunk`) et l'appel à un moteur d'embeddings.

5. **Index vectoriel**
   - Intégrer une base locale comme ChromaDB pour stocker les embeddings.

6. **Pipeline RAG**
   - Construire la chaîne complète de recherche et génération à partir des documents indexés.

## 6. Recommandations de structuration

- Centraliser la configuration OCR dans un seul module et importer l'instance depuis `image_reader.py`.
- Normaliser les exceptions levées par les lecteurs pour faciliter le traitement d'erreurs en amont.
- Ajouter des tests unitaires plus stricts et des tests d'acceptation qui comparent le texte extrait attendu.
- Compléter `requirements.txt` avec les versions exactes utilisées.

---

> Ce document constitue un rapport d'architecture détaillé pour le projet actuel. Il permet de comprendre rapidement les rôles de chaque fichier, l'état des fonctionnalités implémentées et les prochaines priorités pour achever la solution RAG locale.