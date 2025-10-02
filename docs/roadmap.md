## Roadmap

### Phase 0 — Fondations (Semaine 1-2)
- Structurer monorepo, conventions, CI basique, environnements .env
- Schéma Postgres initial, endpoints CRUD profils/offres, upload CV vers S3
- Service `cv-parser` MVP (extraction basique), indexation ES/FAISS initiale

### Phase 1 — MVP Matching (Semaine 3-5)
- Embeddings + FAISS, requêtes ES, fusion résultats, pagination
- API matching candidats↔offres, scoring initial, UI recherche web
- Gradio demo: scénarios de matching reproductibles

### Phase 2 — Agent & Tunnel (Semaine 6-8)
- `llm-agent` (Mistral/OpenAI) pour recherche conversationnelle
- Tunnel de recrutement configurable par poste, suivi de statuts
- Intégration Codility (évaluations), tracking des résultats

### Phase 3 — Durcissement (Semaine 9-10)
- Monitoring, alerting, quotas; durcissement sécurité (PII, journaux)
- Optimisation perfs indexation et requêtes; tuning modèles de scoring

### Phase 4 — Beta privée (Semaine 11+)
- Onboarding recruteurs pilotes, collectes feedbacks, corrections
- Préparation scale (autoscaling, coûts, observabilité)

### Livrables clés
- Web: recherche, fiches profil/offre, favoris, matching
- Mobile: onboarding candidat, profil, candidatures
- Backend: APIs auth, profils, offres, candidatures, matching
- IA: parsing CV, embeddings, scoring
- Search: pipelines ES/FAISS, fusion résultats


