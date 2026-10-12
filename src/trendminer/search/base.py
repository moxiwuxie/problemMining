"""检索后端抽象：为 s1 提供可插拔的实时信息源。

默认使用 NullSearch（不联网，退回模型先验）；配置了密钥后自动切换为真实检索。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class SearchResult:
    dimension: str
    title: str
    url: str
    content: str


class SearchBackend:
    name: str = "null"
    degraded_reason: str = ""

    @property
    def available(self) -> bool:
        """是否真正可联网检索。"""
        return False

    def search(self, query: str, dimension: str, max_results: int) -> List[SearchResult]:
        return []


class NullSearch(SearchBackend):
    """未配置/未启用检索时的占位后端，明确告知降级原因。"""

    name = "null"

    def __init__(self, reason: str = "未启用实时检索，使用模型先验"):
        self.degraded_reason = reason
