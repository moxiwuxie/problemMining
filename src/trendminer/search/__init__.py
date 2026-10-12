"""检索后端工厂：按 settings.search 选择可用后端，不可用时安全降级。"""
from __future__ import annotations

from trendminer.config import Settings
from trendminer.search.base import NullSearch, SearchBackend, SearchResult
from trendminer.search.tavily import TavilySearch

__all__ = ["SearchBackend", "SearchResult", "NullSearch", "TavilySearch", "build_search"]


def build_search(settings: Settings) -> SearchBackend:
    cfg = settings.search
    if not cfg.enabled:
        return NullSearch("实时检索未启用（settings.search.enabled=false），本次基于模型先验")
    if cfg.provider == "tavily":
        backend = TavilySearch(cfg)
        if not backend.available:
            return NullSearch(f"未配置 {cfg.api_key_env}，自动降级为模型先验")
        return backend
    return NullSearch(f"未知检索后端: {cfg.provider}，自动降级为模型先验")
