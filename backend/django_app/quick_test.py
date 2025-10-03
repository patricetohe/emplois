#!/usr/bin/env python
"""
Test rapide du matching - à exécuter avec: python manage.py shell
"""

import os
import sys
from django.conf import settings

# Ajouter le chemin des services IA
ia_services_path = os.path.join(settings.BASE_DIR.parent.parent, 'ia-services', 'matching-engine', 'src')
if ia_services_path not in sys.path:
    sys.path.append(ia_services_path)

def test_matching():
    try:
        from api.models import Candidate, JobOffer
        from api.serializers import CandidateSerializer, JobOfferSerializer
        from matching_service import MatchingService
        
        print("🔍 Vérification des données...")
        candidates_count = Candidate.objects.count()
        jobs_count = JobOffer.objects.count()
        print(f"  Candidats: {candidates_count}, Offres: {jobs_count}")
        
        if candidates_count == 0 or jobs_count == 0:
            print("❌ Pas de données. Exécutez d'abord le seed.")
            return
        
        print("🚀 Initialisation du service de matching...")
        
        # Chemins des index
        candidates_index = os.path.join(settings.BASE_DIR.parent.parent, 'search', 'faiss', 'candidates.index')
        jobs_index = os.path.join(settings.BASE_DIR.parent.parent, 'search', 'faiss', 'job_offers.index')
        
        # Créer les dossiers
        os.makedirs(os.path.dirname(candidates_index), exist_ok=True)
        os.makedirs(os.path.dirname(jobs_index), exist_ok=True)
        
        # Initialiser le service
        matching_service = MatchingService(
            candidates_index_path=candidates_index,
            job_offers_index_path=jobs_index
        )
        
        print("✅ Service initialisé")
        
        # Test avec le premier candidat et la première offre
        candidate = Candidate.objects.first()
        job_offer = JobOffer.objects.first()
        
        print(f"👤 Candidat test: {candidate.first_name} {candidate.last_name}")
        print(f"💼 Offre test: {job_offer.title} @ {job_offer.company}")
        
        # Sérialiser les données
        candidate_data = CandidateSerializer(candidate).data
        job_data = JobOfferSerializer(job_offer).data
        
        # Indexer
        print("📝 Indexation...")
        success1 = matching_service.index_candidate(str(candidate.id), candidate_data)
        success2 = matching_service.index_job_offer(str(job_offer.id), job_data)
        
        if success1 and success2:
            print("✅ Indexation réussie")
            
            # Test de recherche
            print("🔍 Recherche candidats pour l'offre...")
            results = matching_service.find_candidates_for_job(str(job_offer.id), job_data, top_k=3)
            
            print(f"🎯 Trouvé {len(results)} candidats:")
            for candidate_id, score in results:
                try:
                    c = Candidate.objects.get(id=candidate_id)
                    print(f"  - {c.first_name} {c.last_name}: {score:.3f}")
                except:
                    print(f"  - Candidat {candidate_id}: {score:.3f}")
            
            # Statistiques
            stats = matching_service.get_stats()
            print(f"\n📊 Stats: {stats['candidates']['total_vectors']} candidats, {stats['job_offers']['total_vectors']} offres")
            
        else:
            print("❌ Échec de l'indexation")
            
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Installez les dépendances: pip install sentence-transformers faiss-cpu torch")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

# Exécuter le test
test_matching()
