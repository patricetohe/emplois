"""
Vues web pour l'interface de test de l'agent.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json


def agent_test_view(request):
    """Vue pour l'interface de test de l'agent."""
    return render(request, 'agent_test.html')


@csrf_exempt
@require_http_methods(["GET"])
def stats_api(request):
    """API pour récupérer les statistiques des index."""
    try:
        # Importer le service de matching
        from .matching_views import MatchingViewSet
        matching_view = MatchingViewSet()
        matching_view._init_matching_service()
        
        if not matching_view.matching_service:
            return JsonResponse({"error": "Service de matching non disponible"}, status=503)
        
        stats = matching_view.matching_service.get_stats()
        return JsonResponse(stats)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

