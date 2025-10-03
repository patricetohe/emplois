"""
Service d'agent conversationnel pour la recherche (MVP sans appel LLM externe).

Fonctions:
- Détection simple d'intent (offres ↔ candidats) via heuristiques
- Reformulation minimaliste: extraction de mots-clés
- Exécution de la requête vectorielle via FAISS (EmbeddingsProvider)
- Mémoire courte par session (historique basique)
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional

# Dépendances internes (réutilise providers existants du matching-engine)
from embeddings_service import EmbeddingProvider
from faiss_store import FAISSVectorStore
from llm_provider import LLMProvider
from search_provider import SearchProvider


logger = logging.getLogger(__name__)


class AgentMemory:
    """Mémoire courte par session (en mémoire process, MVP)."""

    def __init__(self) -> None:
        self._sessions: Dict[str, List[Dict[str, Any]]]= {}

    def add_turn(self, session_id: str, role: str, content: str) -> None:
        if not session_id:
            return
        self._sessions.setdefault(session_id, []).append({"role": role, "content": content})

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self._sessions.get(session_id, [])


class LLMAgentService:
    """Agent conversationnel minimal branché sur FAISS.

    - Si target == "jobs": retourne des offres pour une requête/candidat
    - Si target == "candidates": retourne des candidats pour une requête/offre
    """

    def __init__(
        self,
        candidates_index_path: str,
        job_offers_index_path: str,
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.embedding_provider = EmbeddingProvider(embedding_model)
        self.dimension = self.embedding_provider.get_embedding_dimension()
        self.candidates_store = FAISSVectorStore(candidates_index_path, self.dimension)
        self.job_offers_store = FAISSVectorStore(job_offers_index_path, self.dimension)
        self.llm = LLMProvider()
        self.search_provider = SearchProvider()
        self.memory = AgentMemory()
        logger.info("LLMAgentService initialisé")

    # ---------- INTENT & PARSING ----------
    @staticmethod
    def _detect_target(query: str, explicit_target: Optional[str]) -> str:
        if explicit_target in {"jobs", "candidates"}:
            return explicit_target
        q = query.lower()
        # Heuristiques simples
        if any(k in q for k in ["offre", "job", "poste", "emplois", "missions"]):
            return "jobs"
        if any(k in q for k in ["candidat", "profil", "talent", "personne"]):
            return "candidates"
        # défaut: recherche d'offres
        return "jobs"

    @staticmethod
    def _extract_keywords(query: str) -> List[str]:
        tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9+#.]+", query)
        stop = {"le", "la", "les", "de", "du", "des", "un", "une", "et", "ou", "pour", "avec",
                "sur", "en", "à", "au", "aux", "d'", "l'", "dans", "par", "chez", "je", "nous",
                "vous", "ils", "elles", "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses"}
        return [t for t in tokens if t.lower() not in stop and len(t) > 1][:20]

    # ---------- EXECUTION ----------
    def _search_jobs_by_text(self, query_text: str, top_k: int) -> List[Tuple[str, float]]:
        vector = self.embedding_provider.embed_single_text(query_text)
        return self.job_offers_store.search("job_offers", vector, top_k)

    def _search_candidates_by_text(self, query_text: str, top_k: int) -> List[Tuple[str, float]]:
        vector = self.embedding_provider.embed_single_text(query_text)
        return self.candidates_store.search("candidates", vector, top_k)

    def ask(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 10,
        target: Optional[str] = None,
        context_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Traite la requête utilisateur et retourne des résultats structurés.

        Args:
            query: question utilisateur en langage naturel
            session_id: identifiant de session pour la mémoire courte
            top_k: nombre de résultats
            target: "jobs" ou "candidates" (optionnel, sinon détection heuristique)
            context_text: texte additionnel (ex: résumé candidat, description offre) pour orienter la recherche
        """
        if not query or not query.strip():
            return {"error": "Requête vide"}

        # Mémoire: log entrée
        if session_id:
            self.memory.add_turn(session_id, "user", query)

        resolved_target = self._detect_target(query, target)
        keywords = self._extract_keywords(query)

        # 1) Reformulation via LLM (si disponible)
        reformulated = None
        if self.llm.is_enabled():
            try:
                reformulated = self.llm.reformulate_query(query, resolved_target)
            except Exception as e:
                logger.warning(f"LLM reformulation échouée: {e}")

        # Texte enrichi pour FAISS et ES
        enriched = reformulated or query
        if keywords:
            enriched += "\nMots-clés: " + ", ".join(keywords)
        if context_text:
            enriched += "\nContexte: " + context_text

        try:
            # 2) FAISS
            if resolved_target == "jobs":
                faiss_results = self._search_jobs_by_text(enriched, top_k)
                index_name = "job_offers"
            else:
                faiss_results = self._search_candidates_by_text(enriched, top_k)
                index_name = "candidates"

            # 3) Elasticsearch (si disponible)
            es_docs: List[Dict[str, Any]] = []
            if self.search_provider.is_enabled():
                try:
                    es_query = self.search_provider.build_text_query(enriched)
                    es_docs = self.search_provider.search(index=index_name, query=es_query, size=top_k)
                except Exception as e:
                    logger.warning(f"Recherche ES échouée: {e}")

            # 4) Fusion simple: priorité à l'intersection, puis union pondérée
            # Normaliser FAISS -> dict id->score
            faiss_map = {doc_id: score for doc_id, score in faiss_results}
            es_map = {}
            for h in es_docs:
                # Try id from _id or _source.id
                doc_id = str(h.get("_id") or h.get("_source", {}).get("id"))
                if doc_id and doc_id != "None":
                    es_map[doc_id] = float(h.get("_score", 1.0))

            # Fusion: score = 0.6*faiss + 0.4*es (si présent), sinon score existant
            fused_ids = set(faiss_map.keys()) | set(es_map.keys())
            fused = []
            for did in fused_ids:
                fa = faiss_map.get(did)
                es = es_map.get(did)
                if fa is not None and es is not None:
                    s = 0.6 * float(fa) + 0.4 * float(es)
                elif fa is not None:
                    s = float(fa)
                else:
                    s = 0.4 * float(es or 0)
                fused.append((did, s))
            fused.sort(key=lambda x: x[1], reverse=True)
            matches = fused[:top_k]

            response: Dict[str, Any] = {
                "target": resolved_target,
                "query": query,
                "reformulated": reformulated,
                "keywords": keywords,
                "matches": matches,
                "top_k": top_k,
                "sources": {
                    "faiss": faiss_results[:top_k],
                    "es": [
                        {"_id": str(h.get("_id")), "_score": h.get("_score")}
                        for h in es_docs[:top_k]
                    ],
                },
            }

            if session_id:
                self.memory.add_turn(session_id, "assistant", f"{resolved_target}:{len(matches)} résultats")
                response["history_len"] = len(self.memory.get_history(session_id))

            return response
        except Exception as e:
            logger.error(f"Erreur agent ask: {e}")
            return {"error": str(e)}


