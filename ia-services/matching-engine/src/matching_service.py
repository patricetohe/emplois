"""
Service de matching principal qui orchestre embeddings et FAISS.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from .embeddings_service import EmbeddingProvider, TextProcessor
from .faiss_store import FAISSVectorStore

logger = logging.getLogger(__name__)


class MatchingService:
    """Service principal de matching candidats ↔ offres."""
    
    def __init__(self, 
                 candidates_index_path: str = "search/faiss/candidates.index",
                 job_offers_index_path: str = "search/faiss/job_offers.index",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialise le service de matching.
        
        Args:
            candidates_index_path: Chemin vers l'index FAISS des candidats
            job_offers_index_path: Chemin vers l'index FAISS des offres
            embedding_model: Modèle d'embedding à utiliser
        """
        self.embedding_provider = EmbeddingProvider(embedding_model)
        self.dimension = self.embedding_provider.get_embedding_dimension()
        
        # Initialiser les vector stores
        self.candidates_store = FAISSVectorStore(candidates_index_path, self.dimension)
        self.job_offers_store = FAISSVectorStore(job_offers_index_path, self.dimension)
        
        logger.info(f"Service de matching initialisé avec dimension {self.dimension}")
    
    def index_candidate(self, candidate_id: str, candidate_data: Dict[str, Any]) -> bool:
        """
        Indexe un candidat dans FAISS.
        
        Args:
            candidate_id: ID du candidat
            candidate_data: Données du candidat (sérialisées)
            
        Returns:
            True si l'indexation a réussi
        """
        try:
            # Préparer le texte du candidat
            text = TextProcessor.prepare_candidate_text(candidate_data)
            if not text.strip():
                logger.warning(f"Candidat {candidate_id}: texte vide, indexation ignorée")
                return False
            
            # Générer l'embedding
            embedding = self.embedding_provider.embed_single_text(text)
            
            # Indexer dans FAISS
            self.candidates_store.upsert("candidates", [candidate_id], [embedding])
            
            logger.info(f"Candidat {candidate_id} indexé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation du candidat {candidate_id}: {e}")
            return False
    
    def index_job_offer(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        """
        Indexe une offre d'emploi dans FAISS.
        
        Args:
            job_id: ID de l'offre
            job_data: Données de l'offre (sérialisées)
            
        Returns:
            True si l'indexation a réussi
        """
        try:
            # Préparer le texte de l'offre
            text = TextProcessor.prepare_job_offer_text(job_data)
            if not text.strip():
                logger.warning(f"Offre {job_id}: texte vide, indexation ignorée")
                return False
            
            # Générer l'embedding
            embedding = self.embedding_provider.embed_single_text(text)
            
            # Indexer dans FAISS
            self.job_offers_store.upsert("job_offers", [job_id], [embedding])
            
            logger.info(f"Offre {job_id} indexée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation de l'offre {job_id}: {e}")
            return False
    
    def find_candidates_for_job(self, 
                               job_id: str, 
                               job_data: Dict[str, Any], 
                               top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Trouve les candidats les plus adaptés pour une offre.
        
        Args:
            job_id: ID de l'offre
            job_data: Données de l'offre
            top_k: Nombre de candidats à retourner
            
        Returns:
            Liste de tuples (candidate_id, score_de_similarité)
        """
        try:
            # Préparer le texte de l'offre
            text = TextProcessor.prepare_job_offer_text(job_data)
            if not text.strip():
                logger.warning(f"Offre {job_id}: texte vide, recherche impossible")
                return []
            
            # Générer l'embedding de l'offre
            job_embedding = self.embedding_provider.embed_single_text(text)
            
            # Rechercher dans l'index des candidats
            results = self.candidates_store.search("candidates", job_embedding, top_k)
            
            logger.info(f"Trouvé {len(results)} candidats pour l'offre {job_id}")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de candidats pour l'offre {job_id}: {e}")
            return []
    
    def find_jobs_for_candidate(self, 
                               candidate_id: str, 
                               candidate_data: Dict[str, Any], 
                               top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Trouve les offres les plus adaptées pour un candidat.
        
        Args:
            candidate_id: ID du candidat
            candidate_data: Données du candidat
            top_k: Nombre d'offres à retourner
            
        Returns:
            Liste de tuples (job_id, score_de_similarité)
        """
        try:
            # Préparer le texte du candidat
            text = TextProcessor.prepare_candidate_text(candidate_data)
            if not text.strip():
                logger.warning(f"Candidat {candidate_id}: texte vide, recherche impossible")
                return []
            
            # Générer l'embedding du candidat
            candidate_embedding = self.embedding_provider.embed_single_text(text)
            
            # Rechercher dans l'index des offres
            results = self.job_offers_store.search("job_offers", candidate_embedding, top_k)
            
            logger.info(f"Trouvé {len(results)} offres pour le candidat {candidate_id}")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche d'offres pour le candidat {candidate_id}: {e}")
            return []
    
    def batch_index_candidates(self, candidates_data: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, bool]:
        """
        Indexe plusieurs candidats en lot.
        
        Args:
            candidates_data: Liste de tuples (candidate_id, candidate_data)
            
        Returns:
            Dictionnaire {candidate_id: success}
        """
        results = {}
        
        # Préparer les textes et embeddings
        texts = []
        ids = []
        
        for candidate_id, candidate_data in candidates_data:
            try:
                text = TextProcessor.prepare_candidate_text(candidate_data)
                if text.strip():
                    texts.append(text)
                    ids.append(candidate_id)
                else:
                    results[candidate_id] = False
            except Exception as e:
                logger.error(f"Erreur préparation candidat {candidate_id}: {e}")
                results[candidate_id] = False
        
        if texts:
            try:
                # Générer tous les embeddings en lot
                embeddings = self.embedding_provider.embed_texts(texts)
                
                # Indexer en lot
                self.candidates_store.upsert("candidates", ids, embeddings)
                
                # Marquer comme succès
                for candidate_id in ids:
                    results[candidate_id] = True
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'indexation en lot: {e}")
                for candidate_id in ids:
                    results[candidate_id] = False
        
        logger.info(f"Indexation en lot terminée: {sum(results.values())}/{len(candidates_data)} succès")
        return results
    
    def batch_index_job_offers(self, jobs_data: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, bool]:
        """
        Indexe plusieurs offres en lot.
        
        Args:
            jobs_data: Liste de tuples (job_id, job_data)
            
        Returns:
            Dictionnaire {job_id: success}
        """
        results = {}
        
        # Préparer les textes et embeddings
        texts = []
        ids = []
        
        for job_id, job_data in jobs_data:
            try:
                text = TextProcessor.prepare_job_offer_text(job_data)
                if text.strip():
                    texts.append(text)
                    ids.append(job_id)
                else:
                    results[job_id] = False
            except Exception as e:
                logger.error(f"Erreur préparation offre {job_id}: {e}")
                results[job_id] = False
        
        if texts:
            try:
                # Générer tous les embeddings en lot
                embeddings = self.embedding_provider.embed_texts(texts)
                
                # Indexer en lot
                self.job_offers_store.upsert("job_offers", ids, embeddings)
                
                # Marquer comme succès
                for job_id in ids:
                    results[job_id] = True
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'indexation en lot: {e}")
                for job_id in ids:
                    results[job_id] = False
        
        logger.info(f"Indexation en lot terminée: {sum(results.values())}/{len(jobs_data)} succès")
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques des index.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        return {
            'candidates': self.candidates_store.get_stats(),
            'job_offers': self.job_offers_store.get_stats(),
            'embedding_dimension': self.dimension,
            'embedding_model': self.embedding_provider.model_name
        }
    
    def delete_candidate(self, candidate_id: str) -> bool:
        """
        Supprime un candidat de l'index.
        
        Args:
            candidate_id: ID du candidat à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        try:
            self.candidates_store.delete("candidates", [candidate_id])
            logger.info(f"Candidat {candidate_id} supprimé de l'index")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du candidat {candidate_id}: {e}")
            return False
    
    def delete_job_offer(self, job_id: str) -> bool:
        """
        Supprime une offre de l'index.
        
        Args:
            job_id: ID de l'offre à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        try:
            self.job_offers_store.delete("job_offers", [job_id])
            logger.info(f"Offre {job_id} supprimée de l'index")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'offre {job_id}: {e}")
            return False
