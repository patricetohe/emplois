"""
Vector store utilisant FAISS pour le stockage et la recherche de similarité.
"""

import os
import pickle
import logging
from typing import List, Tuple, Optional
import numpy as np
import faiss

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """Vector store utilisant FAISS pour la recherche de similarité."""
    
    def __init__(self, index_path: str, dimension: int = 384):
        """
        Initialise le vector store FAISS.
        
        Args:
            index_path: Chemin vers le fichier d'index FAISS
            dimension: Dimension des vecteurs d'embedding
        """
        self.index_path = index_path
        self.dimension = dimension
        self.index = None
        self.id_to_index = {}  # Mapping ID -> index FAISS
        self.index_to_id = {}  # Mapping index FAISS -> ID
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Charge un index existant ou en crée un nouveau."""
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                self._load_mappings()
                logger.info(f"Index FAISS chargé: {self.index_path}")
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de l'index: {e}. Création d'un nouvel index.")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Crée un nouvel index FAISS."""
        # Utiliser IndexFlatIP pour la similarité cosinus
        self.index = faiss.IndexFlatIP(self.dimension)
        logger.info(f"Nouvel index FAISS créé avec dimension {self.dimension}")
    
    def _load_mappings(self):
        """Charge les mappings ID <-> index."""
        mapping_path = self.index_path.replace('.index', '_mappings.pkl')
        if os.path.exists(mapping_path):
            try:
                with open(mapping_path, 'rb') as f:
                    mappings = pickle.load(f)
                    self.id_to_index = mappings.get('id_to_index', {})
                    self.index_to_id = mappings.get('index_to_id', {})
                logger.info(f"Mappings chargés: {len(self.id_to_index)} entrées")
            except Exception as e:
                logger.warning(f"Erreur lors du chargement des mappings: {e}")
                self.id_to_index = {}
                self.index_to_id = {}
    
    def _save_mappings(self):
        """Sauvegarde les mappings ID <-> index."""
        mapping_path = self.index_path.replace('.index', '_mappings.pkl')
        try:
            mappings = {
                'id_to_index': self.id_to_index,
                'index_to_id': self.index_to_id
            }
            with open(mapping_path, 'wb') as f:
                pickle.dump(mappings, f)
            logger.info(f"Mappings sauvegardés: {len(self.id_to_index)} entrées")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des mappings: {e}")
    
    def upsert(self, index_name: str, ids: List[str], vectors: List[np.ndarray]):
        """
        Ajoute ou met à jour des vecteurs dans l'index.
        
        Args:
            index_name: Nom de l'index (pour le préfixe des IDs)
            ids: Liste des IDs des documents
            vectors: Liste des vecteurs d'embedding
        """
        if not ids or not vectors:
            return
        
        if len(ids) != len(vectors):
            raise ValueError("Le nombre d'IDs doit correspondre au nombre de vecteurs")
        
        # Normaliser les vecteurs pour la similarité cosinus
        normalized_vectors = []
        for vector in vectors:
            norm = np.linalg.norm(vector)
            if norm > 0:
                normalized_vectors.append(vector / norm)
            else:
                normalized_vectors.append(vector)
        
        vectors_array = np.array(normalized_vectors).astype('float32')
        
        # Supprimer les anciens vecteurs pour ces IDs
        self.delete(index_name, ids)
        
        # Ajouter les nouveaux vecteurs
        start_idx = self.index.ntotal
        self.index.add(vectors_array)
        
        # Mettre à jour les mappings
        for i, doc_id in enumerate(ids):
            full_id = f"{index_name}:{doc_id}"
            faiss_idx = start_idx + i
            self.id_to_index[full_id] = faiss_idx
            self.index_to_id[faiss_idx] = full_id
        
        # Sauvegarder l'index et les mappings
        self.save()
        logger.info(f"Ajouté {len(ids)} vecteurs à l'index {index_name}")
    
    def search(self, index_name: str, vector: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Recherche les vecteurs les plus similaires.
        
        Args:
            index_name: Nom de l'index à rechercher
            vector: Vecteur de requête
            top_k: Nombre de résultats à retourner
            
        Returns:
            Liste de tuples (ID, score_de_similarité)
        """
        if self.index.ntotal == 0:
            return []
        
        # Normaliser le vecteur de requête
        norm = np.linalg.norm(vector)
        if norm > 0:
            query_vector = (vector / norm).astype('float32').reshape(1, -1)
        else:
            query_vector = vector.astype('float32').reshape(1, -1)
        
        # Recherche
        scores, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx in self.index_to_id:
                full_id = self.index_to_id[idx]
                # Extraire l'ID original (sans le préfixe index_name)
                if full_id.startswith(f"{index_name}:"):
                    doc_id = full_id[len(f"{index_name}:"):]
                    results.append((doc_id, float(score)))
        
        return results
    
    def delete(self, index_name: str, ids: List[str]):
        """
        Supprime des vecteurs de l'index.
        
        Args:
            index_name: Nom de l'index
            ids: Liste des IDs à supprimer
        """
        if not ids:
            return
        
        # Marquer les vecteurs à supprimer
        indices_to_remove = []
        for doc_id in ids:
            full_id = f"{index_name}:{doc_id}"
            if full_id in self.id_to_index:
                faiss_idx = self.id_to_index[full_id]
                indices_to_remove.append(faiss_idx)
                del self.id_to_index[full_id]
                if faiss_idx in self.index_to_id:
                    del self.index_to_id[faiss_idx]
        
        if indices_to_remove:
            # Note: FAISS ne supporte pas la suppression directe
            # On reconstruit l'index sans les vecteurs supprimés
            self._rebuild_index_without_indices(indices_to_remove)
            logger.info(f"Supprimé {len(indices_to_remove)} vecteurs de l'index {index_name}")
    
    def _rebuild_index_without_indices(self, indices_to_remove: List[int]):
        """Reconstruit l'index en excluant certains indices."""
        if not indices_to_remove:
            return
        
        # Récupérer tous les vecteurs sauf ceux à supprimer
        all_vectors = []
        new_mappings = {}
        
        for faiss_idx in range(self.index.ntotal):
            if faiss_idx not in indices_to_remove and faiss_idx in self.index_to_id:
                vector = self.index.reconstruct(faiss_idx)
                all_vectors.append(vector)
                new_mappings[len(all_vectors) - 1] = self.index_to_id[faiss_idx]
        
        # Créer un nouvel index
        if all_vectors:
            vectors_array = np.array(all_vectors).astype('float32')
            new_index = faiss.IndexFlatIP(self.dimension)
            new_index.add(vectors_array)
            self.index = new_index
            
            # Mettre à jour les mappings
            self.index_to_id = new_mappings
            self.id_to_index = {v: k for k, v in new_mappings.items()}
        else:
            # Index vide
            self.index = faiss.IndexFlatIP(self.dimension)
            self.index_to_id = {}
            self.id_to_index = {}
    
    def save(self):
        """Sauvegarde l'index FAISS."""
        try:
            faiss.write_index(self.index, self.index_path)
            self._save_mappings()
            logger.info(f"Index FAISS sauvegardé: {self.index_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'index: {e}")
    
    def get_stats(self) -> dict:
        """
        Retourne les statistiques de l'index.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'mapped_ids': len(self.id_to_index),
            'index_path': self.index_path
        }
