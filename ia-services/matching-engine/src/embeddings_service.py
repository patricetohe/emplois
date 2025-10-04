"""
Service d'embeddings pour générer des vecteurs de représentation des textes.
Utilise sentence-transformers pour créer des embeddings sémantiques.
"""

import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Provider d'embeddings utilisant sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialise le provider d'embeddings.
        
        Args:
            model_name: Nom du modèle sentence-transformers à utiliser
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Charge le modèle sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer
            import torch
            
            # Charger le modèle avec des paramètres pour éviter l'erreur meta tensor
            self.model = SentenceTransformer(
                self.model_name,
                device='cpu',  # Forcer le chargement sur CPU d'abord
                trust_remote_code=False
            )
            
            # S'assurer que le modèle est complètement chargé
            if hasattr(self.model, 'to'):
                self.model.to('cpu')
            
            logger.info(f"Modèle d'embeddings chargé: {self.model_name}")
        except ImportError:
            logger.error("sentence-transformers non installé. Installez avec: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """
        Génère des embeddings pour une liste de textes.
        
        Args:
            texts: Liste des textes à encoder
            
        Returns:
            Liste des vecteurs d'embeddings (numpy arrays)
        """
        if not texts:
            return []
        
        try:
            # Encoder les textes
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
            # S'assurer que c'est une liste de numpy arrays
            if len(embeddings.shape) == 1:
                embeddings = [embeddings]
            else:
                embeddings = [emb for emb in embeddings]
            
            logger.info(f"Généré {len(embeddings)} embeddings de dimension {embeddings[0].shape[0]}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'embeddings: {e}")
            raise
    
    def embed_single_text(self, text: str) -> np.ndarray:
        """
        Génère un embedding pour un seul texte.
        
        Args:
            text: Texte à encoder
            
        Returns:
            Vecteur d'embedding (numpy array)
        """
        return self.embed_texts([text])[0]
    
    def get_embedding_dimension(self) -> int:
        """
        Retourne la dimension des embeddings.
        
        Returns:
            Dimension des vecteurs d'embedding
        """
        if self.model is None:
            raise RuntimeError("Modèle non chargé")
        
        # Générer un embedding de test pour obtenir la dimension
        test_embedding = self.embed_single_text("test")
        return len(test_embedding)


class TextProcessor:
    """Processeur de texte pour préparer les données avant embedding."""
    
    @staticmethod
    def prepare_candidate_text(candidate_data: dict) -> str:
        """
        Prépare le texte d'un candidat pour l'embedding.
        
        Args:
            candidate_data: Dictionnaire contenant les données du candidat
            
        Returns:
            Texte concaténé et nettoyé
        """
        parts = []
        
        # Informations de base
        if candidate_data.get('headline'):
            parts.append(candidate_data['headline'])
        
        if candidate_data.get('summary'):
            parts.append(candidate_data['summary'])
        
        # Compétences
        if candidate_data.get('skills'):
            skills_text = " ".join([skill.get('name', '') for skill in candidate_data['skills']])
            if skills_text:
                parts.append(f"Compétences: {skills_text}")
        
        # Expériences
        if candidate_data.get('experiences'):
            exp_texts = []
            for exp in candidate_data['experiences']:
                exp_parts = []
                if exp.get('title'):
                    exp_parts.append(exp['title'])
                if exp.get('company'):
                    exp_parts.append(exp['company'])
                if exp.get('description'):
                    exp_parts.append(exp['description'])
                if exp_parts:
                    exp_texts.append(" ".join(exp_parts))
            
            if exp_texts:
                parts.append(f"Expériences: {' '.join(exp_texts)}")
        
        # Éducation
        if candidate_data.get('educations'):
            edu_texts = []
            for edu in candidate_data['educations']:
                edu_parts = []
                if edu.get('school'):
                    edu_parts.append(edu['school'])
                if edu.get('degree'):
                    edu_parts.append(edu['degree'])
                if edu.get('field_of_study'):
                    edu_parts.append(edu['field_of_study'])
                if edu_parts:
                    edu_texts.append(" ".join(edu_parts))
            
            if edu_texts:
                parts.append(f"Formation: {' '.join(edu_texts)}")
        
        # CV parsé
        if candidate_data.get('resumes'):
            for resume in candidate_data['resumes']:
                if resume.get('parsed_text'):
                    parts.append(f"CV: {resume['parsed_text']}")
        
        return " ".join(parts)
    
    @staticmethod
    def prepare_job_offer_text(job_data: dict) -> str:
        """
        Prépare le texte d'une offre d'emploi pour l'embedding.
        
        Args:
            job_data: Dictionnaire contenant les données de l'offre
            
        Returns:
            Texte concaténé et nettoyé
        """
        parts = []
        
        # Titre et description
        if job_data.get('title'):
            parts.append(job_data['title'])
        
        if job_data.get('description'):
            parts.append(job_data['description'])
        
        # Compétences requises
        if job_data.get('required_skills'):
            skills_text = " ".join([skill.get('name', '') for skill in job_data['required_skills']])
            if skills_text:
                parts.append(f"Compétences requises: {skills_text}")
        
        # Niveau de séniorité
        if job_data.get('seniority'):
            parts.append(f"Niveau: {job_data['seniority']}")
        
        # Localisation
        if job_data.get('location'):
            parts.append(f"Localisation: {job_data['location']}")
        
        # Remote
        if job_data.get('is_remote'):
            parts.append("Télétravail possible")
        
        return " ".join(parts)
