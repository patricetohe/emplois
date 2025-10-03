"""
Provider LLM (Mistral) via API HTTP.

Configuration via variables d'environnement:
- MISTRAL_API_KEY: clé d'API
- MISTRAL_MODEL: identifiant du modèle (ex: mistral-small-latest)
"""

import os
import logging
from typing import Dict, Any, List, Optional
import requests


logger = logging.getLogger(__name__)


class LLMProvider:
    """Client minimal pour Mistral Chat Completions."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.model = model or os.getenv("MISTRAL_MODEL", "mistral-small-latest")
        self.base_url = os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1/chat/completions")

        if not self.api_key:
            logger.warning("MISTRAL_API_KEY manquant: le LLM sera désactivé")

    def is_enabled(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 512) -> str:
        if not self.is_enabled():
            raise RuntimeError("LLM désactivé: MISTRAL_API_KEY manquant")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Réponse LLM invalide: {e} — {data}")
            raise

    def reformulate_query(self, user_query: str, target: str) -> str:
        """Demande au LLM une reformulation concise optimisée recherche pour target."""
        system = (
            "Tu es un assistant de recherche emploi. Reformule la requête en une phrase optimisée "
            f"pour la recherche {target}. Pas de politesse, pas d'explication."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_query},
        ]
        return self.chat(messages, temperature=0.1, max_tokens=128)


