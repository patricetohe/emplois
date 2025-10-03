"""
SearchProvider minimal pour Elasticsearch (facultatif, activé si ES_URL présent).
"""

import os
import logging
from typing import Dict, Any, List
import requests


logger = logging.getLogger(__name__)


class SearchProvider:
    def __init__(self) -> None:
        self.base_url = os.getenv("ES_URL")  # ex: http://localhost:9200
        self.user = os.getenv("ES_USER")
        self.password = os.getenv("ES_PASSWORD")

    def is_enabled(self) -> bool:
        return bool(self.base_url)

    def search(self, index: str, query: Dict[str, Any], size: int = 10) -> List[Dict[str, Any]]:
        if not self.is_enabled():
            raise RuntimeError("Elasticsearch non configuré (ES_URL)")

        url = f"{self.base_url}/{index}/_search"
        auth = (self.user, self.password) if self.user and self.password else None
        payload = {"query": query, "size": size}
        resp = requests.post(url, json=payload, auth=auth, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        return hits

    @staticmethod
    def build_text_query(text: str) -> Dict[str, Any]:
        return {
            "multi_match": {
                "query": text,
                "fields": ["title^3", "description", "skills^2", "summary", "headline"],
                "type": "best_fields",
            }
        }


