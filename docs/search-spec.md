## Spécification intégration FAISS + Elasticsearch

### Objectif
Fournir une recherche hybride CV↔offres combinant:
- Rappel élevé: Elasticsearch (full-text + filtres)
- Précision: FAISS (similarité vectorielle d’embeddings)
- Fusion: reranking/score final côté service `scoring`

### Pipelines d’indexation
1) Profil candidat créé/mis à jour
   - Normaliser profil (skills, expériences, éducation)
   - Générer embeddings texte (titre, résumé, skills) → vecteur dim=d
   - Upsert dans FAISS (id=candidate_id)
   - Indexer document ES (`candidates`): champs structurés + texte + métadonnées

2) Offre créée/mise à jour
   - Normaliser description, extraire compétences
   - Générer embeddings → upsert FAISS (id=job_offer_id)
   - Indexer ES (`job_offers`)

### Schéma ES (simplifié)
Index `candidates`:
- first_name, last_name (keyword)
- headline, summary (text)
- skills (keyword)
- location (keyword), experience_years (integer), updated_at (date)

Index `job_offers`:
- title, description (text)
- company, location, seniority, is_remote
- required_skills (keyword), posted_at (date)

### Stockage FAISS
- Index IVF_FLAT ou HNSW (selon compromis mémoire/latence)
- Dimension d selon modèle d’embeddings choisi (ex: 384/768)
- Stratégie: un index pour candidats, un autre pour offres

### Requêtes
Recherche candidats pour une offre:
1. ES: filtre location/seniority/skills, récupérer top-K (rappel)
2. FAISS: query par vecteur de l’offre → top-N similaires
3. Fusion: union pondérée + `scoring` (métriques: overlap skills, seniority, distance)

Recherche offres pour un candidat: symétrique.

### Services & API
- `matching-engine` expose:
  - POST /embeddings (batch)
  - POST /faiss/search (index, vector, top_k)
  - POST /faiss/upsert, /faiss/delete
- Django orchestration:
  - Celery tasks: on_save profil/offre → embeddings + ES + FAISS
  - Endpoints recherche/matching → orchestrent ES + FAISS + scoring

### Monitoring
- Latence ES vs FAISS, taux cache, qualité (ctr des résultats, conversions)
- Drifts embeddings: distribution distances, fraîcheur index


