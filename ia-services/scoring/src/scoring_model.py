"""
Modèle de scoring PyTorch pour évaluer la pertinence des matches candidat-offre.
"""

import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Any, Tuple
import pickle
import os

logger = logging.getLogger(__name__)


class ScoringModel(nn.Module):
    """Modèle de scoring pour évaluer la pertinence des matches."""
    
    def __init__(self, 
                 embedding_dim: int = 384,
                 skill_vocab_size: int = 1000,
                 hidden_dim: int = 256,
                 dropout: float = 0.3):
        """
        Initialise le modèle de scoring.
        
        Args:
            embedding_dim: Dimension des embeddings sémantiques
            skill_vocab_size: Taille du vocabulaire des compétences
            hidden_dim: Dimension des couches cachées
            dropout: Taux de dropout
        """
        super(ScoringModel, self).__init__()
        
        self.embedding_dim = embedding_dim
        self.skill_vocab_size = skill_vocab_size
        self.hidden_dim = hidden_dim
        
        # Couches pour les embeddings sémantiques
        self.semantic_linear = nn.Sequential(
            nn.Linear(embedding_dim * 2, hidden_dim),  # Concaténation des embeddings
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Couches pour les compétences
        self.skill_embedding = nn.Embedding(skill_vocab_size, 64)
        self.skill_linear = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Couches pour les features numériques
        self.numeric_linear = nn.Sequential(
            nn.Linear(10, 32),  # 10 features numériques
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Couche de fusion et scoring final
        self.fusion_linear = nn.Sequential(
            nn.Linear(hidden_dim // 2 + 32 + 32, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()  # Score entre 0 et 1
        )
        
    def forward(self, 
                candidate_embedding: torch.Tensor,
                job_embedding: torch.Tensor,
                skill_features: torch.Tensor,
                numeric_features: torch.Tensor) -> torch.Tensor:
        """
        Forward pass du modèle.
        
        Args:
            candidate_embedding: Embedding du candidat
            job_embedding: Embedding de l'offre
            skill_features: Features des compétences
            numeric_features: Features numériques
            
        Returns:
            Score de pertinence (0-1)
        """
        # Traitement des embeddings sémantiques
        semantic_concat = torch.cat([candidate_embedding, job_embedding], dim=-1)
        semantic_features = self.semantic_linear(semantic_concat)
        
        # Traitement des compétences
        skill_emb = self.skill_embedding(skill_features)
        skill_features_processed = self.skill_linear(skill_emb.mean(dim=1))  # Pooling moyen
        
        # Traitement des features numériques
        numeric_features_processed = self.numeric_linear(numeric_features)
        
        # Fusion de toutes les features
        all_features = torch.cat([
            semantic_features, 
            skill_features_processed, 
            numeric_features_processed
        ], dim=-1)
        
        # Score final
        score = self.fusion_linear(all_features)
        return score


class ScoringService:
    """Service de scoring utilisant le modèle PyTorch."""
    
    def __init__(self, model_path: str = None, device: str = 'cpu'):
        """
        Initialise le service de scoring.
        
        Args:
            model_path: Chemin vers le modèle sauvegardé
            device: Device PyTorch à utiliser
        """
        self.device = torch.device(device)
        self.model = None
        self.skill_to_id = {}
        self.id_to_skill = {}
        self.feature_stats = {}
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self._init_default_model()
    
    def _init_default_model(self):
        """Initialise un modèle par défaut."""
        self.model = ScoringModel()
        self.model.to(self.device)
        self.model.eval()
        logger.info("Modèle de scoring par défaut initialisé")
    
    def load_model(self, model_path: str):
        """
        Charge un modèle sauvegardé.
        
        Args:
            model_path: Chemin vers le fichier de modèle
        """
        try:
            checkpoint = torch.load(model_path, map_location=self.device)
            
            # Charger le modèle
            self.model = ScoringModel()
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            # Charger les mappings et statistiques
            self.skill_to_id = checkpoint.get('skill_to_id', {})
            self.id_to_skill = checkpoint.get('id_to_skill', {})
            self.feature_stats = checkpoint.get('feature_stats', {})
            
            logger.info(f"Modèle de scoring chargé depuis {model_path}")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {e}")
            self._init_default_model()
    
    def save_model(self, model_path: str):
        """
        Sauvegarde le modèle.
        
        Args:
            model_path: Chemin de sauvegarde
        """
        try:
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            checkpoint = {
                'model_state_dict': self.model.state_dict(),
                'skill_to_id': self.skill_to_id,
                'id_to_skill': self.id_to_skill,
                'feature_stats': self.feature_stats
            }
            
            torch.save(checkpoint, model_path)
            logger.info(f"Modèle de scoring sauvegardé vers {model_path}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du modèle: {e}")
    
    def extract_features(self, 
                        candidate_data: Dict[str, Any], 
                        job_data: Dict[str, Any],
                        semantic_similarity: float) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Extrait les features pour le scoring.
        
        Args:
            candidate_data: Données du candidat
            job_data: Données de l'offre
            semantic_similarity: Score de similarité sémantique
            
        Returns:
            Tuple (skill_features, numeric_features, semantic_features)
        """
        # Features des compétences
        candidate_skills = set()
        if candidate_data.get('skills'):
            candidate_skills = {skill.get('name', '') for skill in candidate_data['skills']}
        
        job_skills = set()
        if job_data.get('required_skills'):
            job_skills = {skill.get('name', '') for skill in job_data['required_skills']}
        
        # Calculer l'overlap des compétences
        skill_overlap = len(candidate_skills & job_skills)
        skill_ratio = skill_overlap / max(len(job_skills), 1)
        
        # Encoder les compétences (simplifié)
        skill_ids = []
        for skill in list(candidate_skills)[:10]:  # Limiter à 10 compétences
            skill_id = self.skill_to_id.get(skill, 0)
            skill_ids.append(skill_id)
        
        # Padding si nécessaire
        while len(skill_ids) < 10:
            skill_ids.append(0)
        
        skill_features = torch.tensor(skill_ids[:10], dtype=torch.long).unsqueeze(0)
        
        # Features numériques
        numeric_features = torch.tensor([
            semantic_similarity,  # Similarité sémantique
            skill_ratio,  # Ratio d'overlap des compétences
            skill_overlap,  # Nombre de compétences communes
            len(candidate_skills),  # Nombre de compétences candidat
            len(job_skills),  # Nombre de compétences requises
            self._get_experience_years(candidate_data),  # Années d'expérience
            self._get_seniority_match(candidate_data, job_data),  # Match de séniorité
            self._get_location_match(candidate_data, job_data),  # Match de localisation
            self._get_remote_match(candidate_data, job_data),  # Match télétravail
            self._get_education_score(candidate_data)  # Score d'éducation
        ], dtype=torch.float32).unsqueeze(0)
        
        return skill_features, numeric_features, semantic_similarity
    
    def _get_experience_years(self, candidate_data: Dict[str, Any]) -> float:
        """Calcule les années d'expérience du candidat."""
        if not candidate_data.get('skills'):
            return 0.0
        
        total_years = 0.0
        for skill in candidate_data['skills']:
            if isinstance(skill, dict) and 'years_of_experience' in skill:
                total_years += float(skill['years_of_experience'])
        
        return min(total_years / 10.0, 1.0)  # Normaliser sur 10 ans max
    
    def _get_seniority_match(self, candidate_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """Calcule le match de séniorité."""
        job_seniority = job_data.get('seniority', '').lower()
        if not job_seniority:
            return 0.5
        
        # Mapping simplifié des niveaux
        seniority_levels = {
            'intern': 1,
            'junior': 2,
            'mid': 3,
            'senior': 4,
            'lead': 5
        }
        
        job_level = seniority_levels.get(job_seniority, 3)
        
        # Estimer le niveau du candidat basé sur l'expérience
        experience_years = self._get_experience_years(candidate_data) * 10
        if experience_years < 1:
            candidate_level = 1
        elif experience_years < 3:
            candidate_level = 2
        elif experience_years < 5:
            candidate_level = 3
        elif experience_years < 8:
            candidate_level = 4
        else:
            candidate_level = 5
        
        # Score basé sur la proximité des niveaux
        level_diff = abs(job_level - candidate_level)
        return max(0.0, 1.0 - level_diff / 4.0)
    
    def _get_location_match(self, candidate_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """Calcule le match de localisation."""
        candidate_location = candidate_data.get('location', '').lower()
        job_location = job_data.get('location', '').lower()
        
        if not candidate_location or not job_location:
            return 0.5
        
        # Match exact
        if candidate_location == job_location:
            return 1.0
        
        # Match partiel (même ville)
        candidate_city = candidate_location.split(',')[0].strip()
        job_city = job_location.split(',')[0].strip()
        
        if candidate_city == job_city:
            return 0.8
        
        return 0.3  # Localisations différentes
    
    def _get_remote_match(self, candidate_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """Calcule le match télétravail."""
        job_remote = job_data.get('is_remote', False)
        
        # Si l'offre permet le télétravail, c'est toujours un match
        if job_remote:
            return 1.0
        
        # Sinon, dépend de la localisation
        return self._get_location_match(candidate_data, job_data)
    
    def _get_education_score(self, candidate_data: Dict[str, Any]) -> float:
        """Calcule un score d'éducation."""
        if not candidate_data.get('educations'):
            return 0.0
        
        # Score basé sur le nombre d'éducations et la présence de diplômes
        educations = candidate_data['educations']
        score = 0.0
        
        for edu in educations:
            if edu.get('degree'):
                score += 0.5
            if edu.get('field_of_study'):
                score += 0.3
        
        return min(score, 1.0)
    
    def score_match(self, 
                   candidate_data: Dict[str, Any], 
                   job_data: Dict[str, Any],
                   semantic_similarity: float) -> float:
        """
        Calcule le score de pertinence d'un match.
        
        Args:
            candidate_data: Données du candidat
            job_data: Données de l'offre
            semantic_similarity: Score de similarité sémantique
            
        Returns:
            Score de pertinence (0-1)
        """
        try:
            with torch.no_grad():
                # Extraire les features
                skill_features, numeric_features, semantic_sim = self.extract_features(
                    candidate_data, job_data, semantic_similarity
                )
                
                # Créer des embeddings factices pour le modèle (sera remplacé par de vrais embeddings)
                candidate_embedding = torch.randn(1, self.model.embedding_dim)
                job_embedding = torch.randn(1, self.model.embedding_dim)
                
                # Déplacer vers le device
                skill_features = skill_features.to(self.device)
                numeric_features = numeric_features.to(self.device)
                candidate_embedding = candidate_embedding.to(self.device)
                job_embedding = job_embedding.to(self.device)
                
                # Calculer le score
                score = self.model(candidate_embedding, job_embedding, skill_features, numeric_features)
                
                return float(score.item())
                
        except Exception as e:
            logger.error(f"Erreur lors du calcul du score: {e}")
            return 0.0
    
    def score_matches(self, 
                     matches: List[Tuple[Dict[str, Any], Dict[str, Any], float]]) -> List[Tuple[Dict[str, Any], Dict[str, Any], float, float]]:
        """
        Calcule les scores pour une liste de matches.
        
        Args:
            matches: Liste de tuples (candidate_data, job_data, semantic_similarity)
            
        Returns:
            Liste de tuples (candidate_data, job_data, semantic_similarity, relevance_score)
        """
        scored_matches = []
        
        for candidate_data, job_data, semantic_similarity in matches:
            relevance_score = self.score_match(candidate_data, job_data, semantic_similarity)
            scored_matches.append((candidate_data, job_data, semantic_similarity, relevance_score))
        
        # Trier par score de pertinence décroissant
        scored_matches.sort(key=lambda x: x[3], reverse=True)
        
        return scored_matches
