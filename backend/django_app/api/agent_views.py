"""
Vue pour l'agent conversationnel de recherche.
"""

import os
import logging
from typing import Optional

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings


logger = logging.getLogger(__name__)


class AgentViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_service = None
        self._init_agent_service()

    def _init_agent_service(self) -> None:
        try:
            import sys
            ia_matching_path = os.path.join(settings.BASE_DIR.parent.parent, 'ia-services', 'matching-engine', 'src')
            if ia_matching_path not in sys.path:
                sys.path.append(ia_matching_path)

            ia_agent_path = os.path.join(settings.BASE_DIR.parent.parent, 'ia-services', 'llm-agent', 'src')
            if ia_agent_path not in sys.path:
                sys.path.append(ia_agent_path)

            from agent_service import LLMAgentService  # type: ignore

            candidates_index = os.path.join(settings.BASE_DIR.parent.parent, 'search', 'faiss', 'candidates.index')
            jobs_index = os.path.join(settings.BASE_DIR.parent.parent, 'search', 'faiss', 'job_offers.index')
            os.makedirs(os.path.dirname(candidates_index), exist_ok=True)
            os.makedirs(os.path.dirname(jobs_index), exist_ok=True)

            self.agent_service = LLMAgentService(
                candidates_index_path=candidates_index,
                job_offers_index_path=jobs_index,
            )
            logger.info("LLMAgentService initialisé côté Django")
        except Exception as e:
            logger.error(f"Erreur initialisation LLMAgentService: {e}")
            self.agent_service = None

    @action(detail=False, methods=['post'], url_path='ask')
    def ask(self, request):
        if not self.agent_service:
            return Response({"error": "Service agent indisponible"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        query = request.data.get('query')
        session_id: Optional[str] = request.data.get('session_id')
        top_k = int(request.data.get('top_k', 10))
        target = request.data.get('target')  # "jobs" | "candidates" | None
        context_text = request.data.get('context_text')

        try:
            result = self.agent_service.ask(
                query=query,
                session_id=session_id,
                top_k=top_k,
                target=target,
                context_text=context_text,
            )
            return Response(result)
        except Exception as e:
            logger.error(f"Erreur agent ask: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


