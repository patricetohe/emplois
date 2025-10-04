"""
Signals Django pour l'indexation automatique des candidats et offres.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
import os
import sys

from .models import Candidate, JobOffer

logger = logging.getLogger(__name__)


def get_matching_service():
    """Récupère le service de matching (singleton)."""
    try:
        # Ajouter le chemin des services IA au PYTHONPATH
        ia_services_path = os.path.join(settings.BASE_DIR.parent.parent, 'ia-services', 'matching-engine', 'src')
        if ia_services_path not in sys.path:
            sys.path.append(ia_services_path)
        
        from matching_service import MatchingService
        
        # Chemins des index FAISS
        candidates_index = os.path.join(settings.BASE_DIR.parent.parent, 'search', 'faiss', 'candidates.index')
        jobs_index = os.path.join(settings.BASE_DIR.parent.parent, 'search', 'faiss', 'job_offers.index')
        
        # Créer les dossiers si nécessaire
        os.makedirs(os.path.dirname(candidates_index), exist_ok=True)
        os.makedirs(os.path.dirname(jobs_index), exist_ok=True)
        
        return MatchingService(
            candidates_index_path=candidates_index,
            job_offers_index_path=jobs_index
        )
    except Exception as e:
        logger.error(f"Erreur initialisation service matching: {e}")
        return None


@receiver(post_save, sender=Candidate)
def index_candidate_on_save(sender, instance, created, **kwargs):
    """Indexe automatiquement un candidat à la création/modification."""
    try:
        matching_service = get_matching_service()
        if not matching_service:
            logger.warning("Service de matching non disponible pour l'indexation automatique")
            return
        
        # Sérialiser les données du candidat
        from .serializers import CandidateSerializer
        candidate_data = CandidateSerializer(instance).data
        
        success = matching_service.index_candidate(str(instance.id), candidate_data)
        
        if success:
            action = "créé" if created else "mis à jour"
            logger.info(f"Candidat {instance.id} ({instance.first_name} {instance.last_name}) {action} et indexé automatiquement")
        else:
            logger.warning(f"Échec de l'indexation automatique du candidat {instance.id}")
            
    except Exception as e:
        logger.error(f"Erreur indexation automatique candidat {instance.id}: {e}")


@receiver(post_save, sender=JobOffer)
def index_job_offer_on_save(sender, instance, created, **kwargs):
    """Indexe automatiquement une offre à la création/modification."""
    try:
        matching_service = get_matching_service()
        if not matching_service:
            logger.warning("Service de matching non disponible pour l'indexation automatique")
            return
        
        # Sérialiser les données de l'offre
        from .serializers import JobOfferSerializer
        job_data = JobOfferSerializer(instance).data
        
        success = matching_service.index_job_offer(str(instance.id), job_data)
        
        if success:
            action = "créée" if created else "mise à jour"
            logger.info(f"Offre {instance.id} ({instance.title} @ {instance.company}) {action} et indexée automatiquement")
        else:
            logger.warning(f"Échec de l'indexation automatique de l'offre {instance.id}")
            
    except Exception as e:
        logger.error(f"Erreur indexation automatique offre {instance.id}: {e}")


@receiver(post_delete, sender=Candidate)
def remove_candidate_on_delete(sender, instance, **kwargs):
    """Supprime un candidat de l'index à la suppression."""
    try:
        matching_service = get_matching_service()
        if not matching_service:
            return
        
        # Supprimer de l'index FAISS
        matching_service.candidates_store.delete("candidates", [str(instance.id)])
        logger.info(f"Candidat {instance.id} supprimé de l'index automatiquement")
        
    except Exception as e:
        logger.error(f"Erreur suppression automatique candidat {instance.id}: {e}")


@receiver(post_delete, sender=JobOffer)
def remove_job_offer_on_delete(sender, instance, **kwargs):
    """Supprime une offre de l'index à la suppression."""
    try:
        matching_service = get_matching_service()
        if not matching_service:
            return
        
        # Supprimer de l'index FAISS
        matching_service.job_offers_store.delete("job_offers", [str(instance.id)])
        logger.info(f"Offre {instance.id} supprimée de l'index automatiquement")
        
    except Exception as e:
        logger.error(f"Erreur suppression automatique offre {instance.id}: {e}")
