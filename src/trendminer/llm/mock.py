"""Mock LLM 客户端：离线回放 fixtures，使全链路无 API key 可测。"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from trendminer.config import Settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "llm"


class MockLLMClient:
    """与 LLMClient 同接口；按 stage 名读取 fixtures/<stage>.json 回放。"""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        fixtures_dir: Optional[Path] = None,
        seed: Optional[int] = None,
    ):
        self.settings = settings or Settings()
        self.fixtures_dir = Path(fixtures_dir or DEFAULT_FIXTURES_DIR)
        self.seed = seed
        self.calls: List[str] = []

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        stage: Optional[str] = None,
        response_format_json: bool = True,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> str:
        if not stage:
            raise ValueError("MockLLMClient 需要通过 stage 指定回放的 fixture")
        self.calls.append(stage)
        path = self.fixtures_dir / f"{stage}.json"
        if not path.exists():
            raise FileNotFoundError(f"缺少 fixture: {path}")
        data: Any = json.loads(path.read_text(encoding="utf-8"))
        # 轻微扰动，便于验证不同运行/分支的差异
        if self.seed is not None and isinstance(data, dict):
            data = dict(data)
            data.setdefault("_mock_seed", self.seed)
        return json.dumps(data, ensure_ascii=False)
