"""Prompt 加载与渲染。

每个 prompt 文件格式：
---
stage: s1_retrieval
name: 趋势信息检索
temperature: 0.4
---
<系统提示内容>

<!--USER-->
<用户提示模板，可用 {var} 占位符>
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from jinja2 import Template

from trendminer.config import PROMPTS_DIR

_USER_MARKER = "<!--USER-->"


def _split_front_matter(text: str) -> Tuple[Dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text
    meta = yaml.safe_load("\n".join(lines[1:end])) or {}
    body = "\n".join(lines[end + 1 :])
    return meta, body


def _split_body(body: str) -> Tuple[str, str]:
    if _USER_MARKER in body:
        system_part, user_part = body.split(_USER_MARKER, 1)
    else:
        system_part, user_part = "", body
    return system_part.strip(), user_part.strip()


@dataclass
class Prompt:
    stage: str
    name: str
    temperature: float
    system: str
    user_template: str
    meta: Dict[str, Any]

    def render(self, variables: Dict[str, Any]) -> List[Dict[str, str]]:
        system = Template(self.system).render(**variables).strip()
        user = Template(self.user_template).render(**variables).strip()
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        return messages


class PromptLoader:
    def __init__(self, prompts_dir: Optional[Path] = None):
        self.prompts_dir = Path(prompts_dir or PROMPTS_DIR)
        self._cache: Dict[str, Prompt] = {}

    def load_all(self) -> Dict[str, Prompt]:
        if self._cache:
            return self._cache
        for path in sorted(self.prompts_dir.glob("*.md")):
            meta, body = _split_front_matter(path.read_text(encoding="utf-8"))
            stage = meta.get("stage")
            if not stage:
                continue
            system, user = _split_body(body)
            self._cache[stage] = Prompt(
                stage=stage,
                name=meta.get("name", stage),
                temperature=float(meta.get("temperature", 0.4)),
                system=system,
                user_template=user,
                meta=meta,
            )
        return self._cache

    def get(self, stage: str) -> Prompt:
        prompts = self.load_all()
        if stage not in prompts:
            raise KeyError(f"未找到 prompt 阶段: {stage}（已加载: {', '.join(prompts)}）")
        return prompts[stage]
