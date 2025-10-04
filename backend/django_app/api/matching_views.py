"""
Vues pour le matching candidats ↔ offres utilisant les services IA.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
import os

from .models import Candidate, JobOffer
from .serializers import CandidateSerializer, JobOfferSerializer

logger = logging.getLogger(__name__)


class MatchingViewSet(viewsets.ViewSet):
    """ViewSet pour les opérations de matching."""
    permission_classes = [AllowAny]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matching_service = None
        self._init_matching_service()
    
    def _init_matching_service(self):
        """Initialise le service de matching."""
        try:
            # Ajouter le chemin des services IA au PYTHONPATH
            import sys
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
            
            self.matching_service = MatchingService(
                candidates_index_path=candidates_index,
                job_offers_index_path=jobs_index
            )
            logger.info("Service de matching initialisé")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du service de matching: {e}")
            # Ne pas faire échouer l'initialisation, juste désactiver le service
            self.matching_service = None
    
    @action(detail=False, methods=['post'], url_path='index-candidate')
    def index_candidate(self, request):
        """
        Indexe un candidat dans FAISS.
        POST /api/matching/index-candidate/
        Body: {"candidate_id": 123}
        """
        if not self.matching_service:
            return Response(
                {"error": "Service de matching non disponible"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        candidate_id = request.data.get('candidate_id')
        if not candidate_id:
            return Response(
                {"error": "candidate_id requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            candidate = Candidate.objects.get(id=candidate_id)
            candidate_data = CandidateSerializer(candidate).data
            
            success = self.matching_service.index_candidate(str(candidate_id), candidate_data)
            
            if success:
                return Response({"message": f"Candidat {candidate_id} indexé avec succès"})
            else:
                return Response(
                    {"error": "Échec de l'indexation"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Candidate.DoesNotExist:
            return Response(
                {"error": "Candidat non trouvé"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur indexation candidat {candidate_id}: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='index-job-offer')
    def index_job_offer(self, request):
        """
        Indexe une offre d'emploi dans FAISS.
        POST /api/matching/index-job-offer/
        Body: {"job_offer_id": 456}
        """
        if not self.matching_service:
            return Response(
                {"error": "Service de matching non disponible"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        job_offer_id = request.data.get('job_offer_id')
        if not job_offer_id:
            return Response(
                {"error": "job_offer_id requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            job_offer = JobOffer.objects.get(id=job_offer_id)
            job_data = JobOfferSerializer(job_offer).data
            
            success = self.matching_service.index_job_offer(str(job_offer_id), job_data)
            
            if success:
                return Response({"message": f"Offre {job_offer_id} indexée avec succès"})
            else:
                return Response(
                    {"error": "Échec de l'indexation"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except JobOffer.DoesNotExist:
            return Response(
                {"error": "Offre non trouvée"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur indexation offre {job_offer_id}: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='find-candidates-for-job')
    def find_candidates_for_job(self, request):
        """
        Trouve les candidats les plus adaptés pour une offre.
        POST /api/matching/find-candidates-for-job/
        Body: {"job_offer_id": 456, "top_k": 10}
        """
        if not self.matching_service:
            return Response(
                {"error": "Service de matching non disponible"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        job_offer_id = request.data.get('job_offer_id')
        top_k = request.data.get('top_k', 10)
        
        if not job_offer_id:
            return Response(
                {"error": "job_offer_id requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            job_offer = JobOffer.objects.get(id=job_offer_id)
            job_data = JobOfferSerializer(job_offer).data
            
            results = self.matching_service.find_candidates_for_job(
                str(job_offer_id), job_data, top_k
            )
            
            # Enrichir avec les données des candidats
            enriched_results = []
            for candidate_id, score in results:
                try:
                    candidate = Candidate.objects.get(id=candidate_id)
                    candidate_data = CandidateSerializer(candidate).data
                    enriched_results.append({
                        'candidate': candidate_data,
                        'score': score,
                        'candidate_id': candidate_id
                    })
                except Candidate.DoesNotExist:
                    logger.warning(f"Candidat {candidate_id} non trouvé en base")
                    continue
            
            return Response({
                'job_offer': job_data,
                'matches': enriched_results,
                'total_matches': len(enriched_results)
            })
            
        except JobOffer.DoesNotExist:
            return Response(
                {"error": "Offre non trouvée"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur recherche candidats pour offre {job_offer_id}: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='find-jobs-for-candidate')
    def find_jobs_for_candidate(self, request):
        """
        Trouve les offres les plus adaptées pour un candidat.
        POST /api/matching/find-jobs-for-candidate/
        Body: {"candidate_id": 123, "top_k": 10}
        """
        if not self.matching_service:
            return Response(
                {"error": "Service de matching non disponible"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        candidate_id = request.data.get('candidate_id')
        top_k = request.data.get('top_k', 10)
        
        if not candidate_id:
            return Response(
                {"error": "candidate_id requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            candidate = Candidate.objects.get(id=candidate_id)
            candidate_data = CandidateSerializer(candidate).data
            
            results = self.matching_service.find_jobs_for_candidate(
                str(candidate_id), candidate_data, top_k
            )
            
            # Enrichir avec les données des offres
            enriched_results = []
            for job_id, score in results:
                try:
                    job_offer = JobOffer.objects.get(id=job_id)
                    job_data = JobOfferSerializer(job_offer).data
                    enriched_results.append({
                        'job_offer': job_data,
                        'score': score,
                        'job_offer_id': job_id
                    })
                except JobOffer.DoesNotExist:
                    logger.warning(f"Offre {job_id} non trouvée en base")
                    continue
            
            return Response({
                'candidate': candidate_data,
                'matches': enriched_results,
                'total_matches': len(enriched_results)
            })
            
        except Candidate.DoesNotExist:
            return Response(
                {"error": "Candidat non trouvé"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur recherche offres pour candidat {candidate_id}: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='batch-index-candidates')
    def batch_index_candidates(self, request):
        """
        Indexe plusieurs candidats en lot.
        POST /api/matching/batch-index-candidates/
        Body: {"candidate_ids": [1, 2, 3]}
        """
        if not self.matching_service:
            return Response(
                {"error": "Service de matching non disponible"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        candidate_ids = request.data.get('candidate_ids', [])
        if not candidate_ids:
            return Response(
                {"error": "candidate_ids requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Récupérer les candidats
            candidates = Candidate.objects.filter(id__in=candidate_ids)
            candidates_data = [
                (str(candidate.id), CandidateSerializer(candidate).data)
                for candidate in candidates
            ]
            
            results = self.matching_service.batch_index_candidates(candidates_data)
            
            return Response({
                'results': results,
                'total_processed': len(candidates_data),
                'successful': sum(results.values())
            })
            
        except Exception as e:
            logger.error(f"Erreur indexation en lot candidats: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='batch-index-job-offers')
    def batch_index_job_offers(self, request):
        """
        Indexe plusieurs offres en lot.
        POST /api/matching/batch-index-job-offers/
        Body: {"job_offer_ids": [1, 2, 3]}
        """
        if not self.matching_service:
            return Response(
                {"error": "Service de matching non disponible"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        job_offer_ids = request.data.get('job_offer_ids', [])
        if not job_offer_ids:
            return Response(
                {"error": "job_offer_ids requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Récupérer les offres
            job_offers = JobOffer.objects.filter(id__in=job_offer_ids)
            jobs_data = [
                (str(job.id), JobOfferSerializer(job).data)
                for job in job_offers
            ]
            
            results = self.matching_service.batch_index_job_offers(jobs_data)
            
            return Response({
                'results': results,
                'total_processed': len(jobs_data),
                'successful': sum(results.values())
            })
            
        except Exception as e:
            logger.error(f"Erreur indexation en lot offres: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='stats')
    def get_stats(self, request):
        """
        Retourne les statistiques des index.
        GET /api/matching/stats/
        """
        if not self.matching_service:
            return Response(
                {"error": "Service de matching non disponible"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            stats = self.matching_service.get_stats()
            return Response(stats)
        except Exception as e:
            logger.error(f"Erreur récupération stats: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
