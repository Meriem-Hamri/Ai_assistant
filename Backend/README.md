# 🤖 Assistant AI - Recherche documentaire locale avec RAG

Assistant AI est une application de recherche documentaire et de question-réponse locale, conçue pour importer des fichiers PDF, DOCX, images et scans, les traiter localement, les indexer dans un moteur vectoriel, puis y répondre via un modèle LLM exécuté sur la machine.

Le projet fonctionne entièrement en local, sans dépendance au cloud pour la génération de réponses. Il combine :

- un backend FastAPI pour l'API et la logique métier ;
- un frontend Next.js / React / TypeScript pour l'interface utilisateur ;
- PostgreSQL pour la persistance des métadonnées et des conversations ;
- Redis + Celery pour les tâches asynchrones de traitement documentaire ;
- ChromaDB pour le stockage vectoriel et la recherche sémantique ;
- Ollama avec un modèle local Qwen pour la génération de réponses ;
- BGE-M3 pour les embeddings, avec des modèles de détection et d'extraction de texte locale.

---

## 🧩 Stack technique actuelle

### Backend
- Python 3.10+
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Alembic
- Celery
- Redis
- ChromaDB
- Ollama
- PyMuPDF
- python-docx
- Pillow
- PaddleOCR
- PyTesseract
- sentence-transformers / BGE-M3
- pytest

### Frontend
- Next.js
- React
- TypeScript
- DOMPurify
- Mammoth

### Infrastructure / orchestration
- Docker Compose
- Turbo monorepo
- npm workspaces

---

## 🏗️ Architecture du système

```mermaid
graph TD
    A[Utilisateur] --> B[Frontend Next.js]
    B --> C[FastAPI API]
    C --> D[DocumentService]
    D --> E[Celery worker]
    E --> F[Extraction / OCR / Metadata]
    F --> G[Chunking & embeddings]
    G --> H[ChromaDB]
    C --> I[PostgreSQL]
    C --> J[Conversation & messages]
    H --> K[Recherche vectorielle]
    K --> L[PromptBuilder]
    L --> M[Ollama / Qwen]
    M --> A
```

### Flux principal
1. Un document est uploadé via l'API FastAPI.
2. Le document est enregistré en base PostgreSQL avec ses métadonnées.
3. Un worker Celery traite le document de manière asynchrone.
4. Le système extrait le texte, reconnaît les métadonnées et prépare les chunks.
5. Les embeddings sont générés avec le modèle BGE-M3.
6. Les fragments sont envoyés dans ChromaDB.
7. L'utilisateur pose une question via le frontend.
8. Le backend recherche les passages pertinents et construit un prompt RAG.
9. Le modèle local Qwen répond avec le contexte documentaire.

---

## 📁 Structure du dépôt

```text
.
├── Backend/
│   ├── app/
│   ├── docs/
│   ├── tests/
│   ├── alembic/
│   ├── .env.example
│   ├── Dockerfile.worker
│   ├── requirements.txt
│   ├── README.md
│   └── ...
├── Frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── package.json
│   └── ...
├── compose.yaml
├── package.json
├── turbo.json
├── ARCHITECTURE.md
└── .env.example
```

---

## ⚙️ Prérequis

Avant de lancer le projet, vérifiez que vous avez :

- Python 3.10 ou plus
- Node.js 18+
- npm
- Docker Desktop ou Docker Engine
- Git
- Accès réseau pour télécharger les dépendances et les modèles localement

Pour le modèle LLM local, le projet s'appuie sur Ollama. Il est nécessaire de démarrer Ollama et de télécharger le modèle utilisé par le backend.

---

## 🔐 Variables d'environnement

Copiez le fichier d'exemple et personnalisez-le :

```bash
copy .env.example .env
```

Exemple de configuration :

```env
POSTGRES_DB=assistant_ai
POSTGRES_USER=assistant_user
POSTGRES_PASSWORD=change_me
DATABASE_URL=postgresql+psycopg://assistant_user:change_me@localhost:5432/assistant_ai
CHROMA_HOST=localhost
CHROMA_PORT=8001
REDIS_URL=redis://localhost:6379/0
```

Le backend est également configurable via les variables d'environnement exposées par les services Docker et les fichiers de configuration Python.

---

## 🚀 Démarrage rapide

### 1) Installer les dépendances racine

```bash
npm install
```

### 2) Démarrer les services de données

```bash
docker compose up -d postgres chroma redis
```

Cela démarre :
- PostgreSQL sur le port 5432
- ChromaDB sur le port 8001
- Redis sur le port 6379

### 3) Installer les dépendances Python du backend

```bash
cd Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4) Démarrer Ollama et le modèle local

```bash
ollama pull qwen3:4b-instruct
```

Puis vérifiez le service Ollama disponible localement sur le port 11434.

### 5) Lancer le backend

```bash
cd Backend
python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 6) Lancer le frontend

```bash
cd Frontend
npm install
npm run dev
```

Le frontend est typiquement disponible sur :
- http://localhost:3000

L'API est disponible sur :
- http://localhost:8000

---

## 🐳 Démarrage via Docker

Le projet inclut un fichier Docker Compose complet pour les services nécessaires au traitement documentaire.

```bash
docker compose up -d
```

Services fournis :
- `postgres` : base documentaire et conversationnelle
- `chroma` : moteur de recherche vectorielle
- `redis` : broker Celery
- `worker` : traitement asynchrone des documents

Le service `worker` utilise les variables suivantes :
- `REDIS_URL`
- `DATABASE_URL`
- `CHROMA_HOST`
- `CHROMA_PORT`
- `OLLAMA_HOST`

---

## 🧠 Fonctionnalités principales

### Gestion documentaire
- upload de fichiers PDF, DOCX et images
- stockage physique des fichiers
- métadonnées métier (titre, type, catégorie, personne, année, tags, etc.)
- suivi du statut des documents (queued, processing, ready, error)
- consultation des fichiers dans l'API
- suppression avec contrainte métier si un document est encore utilisé

### Extraction de contenu
- extraction PDF textuelle via PyMuPDF
- extraction DOCX via python-docx
- OCR avec PaddleOCR pour les images et scans
- détection du format du document
- ouverture de fichiers déjà stockés côté backend

### Traitement asynchrone
- tâches Celery pour la transformation des documents
- traitement découplé du flux de requêtes HTTP
- intégration avec Redis et la file d'attente

### RAG local
- génération d'embeddings avec BGE-M3
- stockage vectoriel dans ChromaDB
- recherche sémantique sur les chunks les plus pertinents
- construction du prompt RAG
- réponse générée par Ollama / Qwen
- retour de la réponse plus ses sources

### Chat et conversations
- création et gestion de conversations
- stockage des messages utilisateur/assistant
- historique en base PostgreSQL
- filtrage documentaire par conversation et documents associés

---

## 🧪 Tests et validation

Le projet dispose d'une suite de tests Python organisé autour de pytest.

### Lancer tous les tests

```bash
cd Backend
python -m pytest -q
```

### Lancer un sous-ensemble

```bash
cd Backend
python -m pytest tests/test_chat_service.py -q
python -m pytest tests/test_chroma_store.py -q
python -m pytest tests/test_document_lifecycle.py -q
```

### Vérifier rapidement le backend

```bash
cd Backend
python -m pytest tests/test_rag_pipeline.py -q
```

Les tests couvrent notamment :
- l'API FastAPI ;
- les services de documents ;
- le pipeline RAG ;
- ChromaDB ;
- les conversations ;
- les tâches Celery ;
- l'extraction de documents ;
- le traitement OCR / metadata.

---

## 🛠️ Commandes utiles

### Backend

```bash
cd Backend
python -m uvicorn app.api.main:app --reload
python -m pytest -q
```

### Frontend

```bash
cd Frontend
npm install
npm run dev
npm run build
npm run lint
```

### Docker

```bash
docker compose up -d
docker compose logs -f worker
docker compose down
```

---

## 🧭 Points d'architecture importants

Le dépôt suit une séparation claire entre :

- `app/api` : routes et schémas HTTP
- `app/documents` : lifecycle des documents, upload, enregistrement et traitement
- `app/conversations` : gestion des conversations et des messages
- `app/rag` : pipeline de retrieval + génération
- `app/vectorstore` : intégration ChromaDB
- `app/embeddings` : génération d'embeddings
- `app/llm` : client Ollama / LLM local
- `app/metadata` : extraction et normalisation de métadonnées
- `app/tasks` : tâches Celery
- `app/database` : modèles SQLAlchemy et session

---

## 📚 Documentation complémentaire

- [ARCHITECTURE.md](../ARCHITECTURE.md) : vue d'ensemble de l'architecture et des composants.
- [Backend/docs/STEP_BY_STEP.md](docs/STEP_BY_STEP.md) : guide pas à pas pour l'installation, les tests et le dépannage.
- [Backend/RAG.md](RAG.md) : documentation détaillée du pipeline RAG.

---

## ✅ État du projet

Le projet est actuellement orienté vers une architecture de production locale de type RAG documentaire :

- interface web fonctionnelle ;
- backend API opérationnel ;
- base de données structurée ;
- moteur vectoriel intégré ;
- pipeline de traitement documentaire asynchrone ;
- génération de réponses locale via Ollama ;
- infrastructure dockerisée pour un lancement rapide.

Il est prêt pour le développement de fonctionnalités métier complémentaires, la stabilisation du flux OCR, la fin du pipeline de chunking et l'industrialisation du déploiement local.

---

> Ce README est un point d'entrée complet pour comprendre le projet, le lancer localement, et suivre le cycle de développement complet du système Assistant AI.