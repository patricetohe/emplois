## Spécification couche IA

### Composants
- cv-parser: extraction texte + champs structurés (nom, email, skills, expériences)
- matching-engine: embeddings + FAISS + règles de similarité
- scoring: modèle ML (PyTorch) pour reranking multi-signal
- llm-agent: interface conversationnelle (Mistral/OpenAI), reformulation requêtes, intents

### Abstractions (contrats)
`EmbeddingProvider`:
- `embed_texts(texts: List[str]) -> List[Vector]`

`VectorStore` (FAISS):
- `upsert(index: str, ids: List[str], vectors: List[Vector])`
- `search(index: str, vector: Vector, top_k: int) -> List[(id, distance)]`
- `delete(index: str, ids: List[str])`

`SearchProvider` (ES):
- `search(index: str, query: dict, top_k: int) -> List[Doc]`

`ScoringModel`:
- `score(match_context) -> float` (features: distance, overlap skills, seniority gap, geo, signaux métier)

`LLMAgent`:
- `answer(query, tools=[ES, FAISS]) -> response` (toolformer style simplifié)

### Parcours requête conversationnelle
1) Détection d’intent (recherche candidats/offres, filtrage, tri)
2) Reformulation en requête structurée (filtres ES + embedding query)
3) Exécution ES + FAISS, fusion via `scoring`
4) Génération réponse (citations, critères appliqués, actions rapides)

### Modèles/Infra
- Embeddings: `sentence-transformers` (all-MiniLM-L6-v2 ou bge-small), dimension d=384/768
- LLM: Mistral open source (local/EC2) + OpenAI (tests/ablation)
- Déploiement: services découplés, gRPC/HTTP, queues Celery pour tâches lourdes


