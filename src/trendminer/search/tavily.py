"""Tavily 检索后端（OpenAI 生态常用的搜索 API，单一 API key 即可用）。"""
from __future__ import annotations

from typing import List

import requests

from trendminer.config import SearchConfig
from trendminer.search.base import SearchBackend, SearchResult

TAVILY_ENDPOINT = "https://api.tavily.com/search"


class TavilySearch(SearchBackend):
    name = "tavily"

    def __init__(self, config: SearchConfig):
        self.config = config

    @property
    def available(self) -> bool:
        return bool(self.config.api_key)

    def search(self, query: str, dimension: str, max_results: int) -> List[SearchResult]:
        if not self.available:
            return []
        payload = {
            "api_key": self.config.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
        }
        try:
            resp = requests.post(TAVILY_ENDPOINT, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError):
            return []

        results: List[SearchResult] = []
        for item in (data.get("results") or [])[:max_results]:
            results.append(
                SearchResult(
                    dimension=dimension,
                    title=str(item.get("title") or ""),
                    url=str(item.get("url") or ""),
                    content=str(item.get("content") or "").strip(),
                )
            )
        return results
