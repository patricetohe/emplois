#!/usr/bin/env python
"""
Script de test pour valider le service de matching.
Usage: python manage.py shell < test_matching.py
"""

import os
import sys
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ajouter le chemin des services IA
import django
from django.conf import settings
ia_services_path = os.path.join(settings.BASE_DIR.parent, 'ia-services', 'matching-engine', 'src')
sys.path.append(ia_services_path)

from api.models import Candidate, JobOffer, Skill
from api.serializers import CandidateSerializer, JobOfferSerializer

def test_matching_service():
    """Test du service de matching."""
    try:
        from matching_service import MatchingService
        
        # Initialiser le service
        candidates_index = os.path.join(settings.BASE_DIR.parent, 'search', 'faiss', 'candidates.index')
        jobs_index = os.path.join(settings.BASE_DIR.parent, 'search', 'faiss', 'job_offers.index')
        
        # Créer les dossiers si nécessaire
        os.makedirs(os.path.dirname(candidates_index), exist_ok=True)
        os.makedirs(os.path.dirname(jobs_index), exist_ok=True)
        
        matching_service = MatchingService(
            candidates_index_path=candidates_index,
            job_offers_index_path=jobs_index
        )
        
        print("✅ Service de matching initialisé")
        
        # Récupérer quelques candidats et offres
        candidates = Candidate.objects.all()[:3]
        job_offers = JobOffer.objects.all()[:3]
        
        if not candidates:
            print("❌ Aucun candidat trouvé. Exécutez d'abord le script de seed.")
            return
        
        if not job_offers:
            print("❌ Aucune offre trouvée. Exécutez d'abord le script de seed.")
            return
        
        print(f"📊 Test avec {len(candidates)} candidats et {len(job_offers)} offres")
        
        # Test d'indexation des candidats
        print("\n🔍 Test d'indexation des candidats...")
        for candidate in candidates:
            candidate_data = CandidateSerializer(candidate).data
            success = matching_service.index_candidate(str(candidate.id), candidate_data)
            if success:
                print(f"  ✅ Candidat {candidate.id} ({candidate.first_name} {candidate.last_name}) indexé")
            else:
                print(f"  ❌ Échec indexation candidat {candidate.id}")
        
        # Test d'indexation des offres
        print("\n🔍 Test d'indexation des offres...")
        for job_offer in job_offers:
            job_data = JobOfferSerializer(job_offer).data
            success = matching_service.index_job_offer(str(job_offer.id), job_data)
            if success:
                print(f"  ✅ Offre {job_offer.id} ({job_offer.title} @ {job_offer.company}) indexée")
            else:
                print(f"  ❌ Échec indexation offre {job_offer.id}")
        
        # Test de recherche candidats pour une offre
        print("\n🔍 Test de recherche candidats pour une offre...")
        test_job = job_offers[0]
        job_data = JobOfferSerializer(test_job).data
        results = matching_service.find_candidates_for_job(str(test_job.id), job_data, top_k=5)
        
        print(f"  📋 Offre test: {test_job.title} @ {test_job.company}")
        print(f"  🎯 Trouvé {len(results)} candidats:")
        for candidate_id, score in results:
            try:
                candidate = Candidate.objects.get(id=candidate_id)
                print(f"    - {candidate.first_name} {candidate.last_name} (score: {score:.3f})")
            except Candidate.DoesNotExist:
                print(f"    - Candidat {candidate_id} (score: {score:.3f}) - non trouvé en base")
        
        # Test de recherche offres pour un candidat
        print("\n🔍 Test de recherche offres pour un candidat...")
        test_candidate = candidates[0]
        candidate_data = CandidateSerializer(test_candidate).data
        results = matching_service.find_jobs_for_candidate(str(test_candidate.id), candidate_data, top_k=5)
        
        print(f"  👤 Candidat test: {test_candidate.first_name} {test_candidate.last_name}")
        print(f"  🎯 Trouvé {len(results)} offres:")
        for job_id, score in results:
            try:
                job_offer = JobOffer.objects.get(id=job_id)
                print(f"    - {job_offer.title} @ {job_offer.company} (score: {score:.3f})")
            except JobOffer.DoesNotExist:
                print(f"    - Offre {job_id} (score: {score:.3f}) - non trouvée en base")
        
        # Statistiques
        print("\n📊 Statistiques des index:")
        stats = matching_service.get_stats()
        print(f"  Candidats indexés: {stats['candidates']['total_vectors']}")
        print(f"  Offres indexées: {stats['job_offers']['total_vectors']}")
        print(f"  Dimension embeddings: {stats['embedding_dimension']}")
        print(f"  Modèle: {stats['embedding_model']}")
        
        print("\n✅ Tests de matching terminés avec succès!")
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Installez les dépendances avec: pip install -r ia-services/requirements.txt")
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        logger.exception("Détails de l'erreur:")

if __name__ == "__main__":
    test_matching_service()
