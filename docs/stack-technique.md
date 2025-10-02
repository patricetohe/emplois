## Stack technique et arguments

### Frontend
- React (possible Next.js) : écosystème mature, SSR/ISR pour SEO et perfs.
- UI: Tailwind ou MUI; State: Redux Toolkit ou Zustand; Form: React Hook Form.

### Mobile
- React Native: mutualisation logique/UX, déploiement iOS/Android rapide.

### Backend
- Django + Django REST Framework: productivité, sécurité, admin par défaut.
- Auth: djangorestframework-simplejwt (ou auth sessions) selon besoin web/mobile.
- Asynchronisme: Celery + Redis pour tâches lourdes (parsing, embeddings, indexation).

### IA / ML
- Mistral (open-source) et OpenAI (tests): flexibilité coût/qualité, fallback.
- Frameworks: PyTorch et/ou TensorFlow selon modèles.
- Embeddings: sentence-transformers; stockage FAISS pour similarité dense.
- Scoring: pipeline PyTorch (features textuelles + signaux métier) exportable TorchScript.

### Recherche
- Elasticsearch: filtres structurés, full-text, agrégations, tri multi-critères.
- FAISS: ANN haute performance pour similarité CV↔offre.
- Stratégie hybride: ES pour rappel + FAISS pour précision, fusion par `scoring`.

### Données
- PostgreSQL (RDS): transactions, contraintes fortes, SQL riche.
- S3: stockage CV/fichiers; presigned URLs pour upload/download sécurisé.
- Schéma initial: candidats, expériences, compétences, offres, candidatures, workflows.

### Intégrations tests
- Codility (phase 1), solution interne plus tard (exécuteurs isolés, sandboxing).

### Observabilité & Qualité
- Logging structuré (JSON), traces (OpenTelemetry), métriques (Prometheus/Grafana).
- Tests: PyTest (backend), Jest/RTL (frontend), Detox (mobile), notebooks pour R&D.

### Dev, CI/CD, Infra
- Node 20+, Python 3.11+, Docker; gestion deps: pip/poetry + npm/yarn.
- GitHub Actions: lint, tests, build images, scans SCA; déploiement sur AWS.
- Orchestration: Kubernetes (EKS) + Helm; secrets via AWS Secrets Manager.


