## Architecture cible (haut niveau)

### Composants
- Frontend web: React (Next.js possible) → UI candidats/recruteurs
- Mobile: React Native → parcours candidat mobile-first
- Backend API: Django + Django REST Framework → logique métier, auth, workflows
- IA services:
  - matching-engine: génération d’embeddings/proximité, règles de pondération
  - scoring: modèles TF/PyTorch pour score de pertinence et fiabilité
  - llm-agent: orchestration d’appels Mistral/OpenAI pour recherche conversationnelle
  - cv-parser: extraction de profils à partir de CV (pdf/doc/txt)
- Recherche sémantique: FAISS (similarité) + Elasticsearch (recherche textuelle/filtrée)
- Données: PostgreSQL (gestion métier) + S3 (fichiers CV, exports)
- Observabilité: logs, métriques, traçage (OpenTelemetry possible)
- CI/CD: GitHub Actions
- Infra: Docker, Kubernetes, AWS (EC2/EKS, S3, RDS, IAM)

### Flux principaux
1) Onboarding candidat
   - Upload CV → `cv-parser` → normalisation profil → stockage Postgres + S3
   - Embeddings profil (matching-engine) → index FAISS → document enrichi Elasticsearch

2) Publication offre (recruteur)
   - Création offre → Postgres → embeddings → index FAISS + ES → règles de visibilité

3) Matching & recherche
   - Requête: mots-clés/critères ou question naturelle → `llm-agent`
   - `llm-agent` appelle ES (filtre) + FAISS (similarité) → fusion/tri via `scoring`
   - Résultats paginés → UI + options (sauvegarde, workflow, évaluation)

4) Tunnel de recrutement
   - Étapes configurables par poste (screening, test, entretien, offre)
   - Intégrations tests (Codility ou interne) + suivi statuts

### Schéma logique (texte)
UI (Web/Mobile)
  ↕
API Django (auth, profils, offres, candidatures, workflow)
  ↕               ↘
PostgreSQL        IA services (cv-parser, matching, scoring, llm-agent)
  ↕               ↘
Elasticsearch  ←→ FAISS
  ↕
S3 (CV)

### Arborescence cible (proposée)
```
bassin_emplois/
  backend/
    django_app/                     # projet Django existant (core + api)
    src/
      api/                          # clients externes si besoin
      auth/
      database/
      models/
      services/
        matching_engine/
        scoring/
        cv_parser/
        llm_agent/
      utils/
    tests/
  frontend/
    src/
      components/
      pages/
      services/
      store/
      utils/
  ia-services/
    matching-engine/
    scoring/
    cv-parser/
    llm-agent/
  search/
    elasticsearch/
    faiss/
  demos/
    gradio/
  devops/
    k8s/
  docs/
```

### Contrats d’API (extraits)
- Auth: JWT (ou session) via Django/DRF
- Profils: CRUD, import CV (multipart), statut de complétude
- Offres: CRUD, critères, tags compétences, seniorité
- Matching: endpoints pour suggestions candidats↔offres, pagination, filtres
- Recherche: query textuelle + filtres structurés; agrégations

### Sécurité & conformité (haut niveau)
- Séparation données PII, chiffrement au repos (RDS, S3) et en transit (TLS)
- Journalisation accès/exports, gestion des rôles (recruteur, admin, candidat)
- Réversibilité des données (exports), suppression sur demande


