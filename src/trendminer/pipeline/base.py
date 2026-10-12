"""阶段通用工具：调用 LLM、解析、落盘（含 resume）。"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from trendminer.context import PipelineContext
from trendminer.llm.parser import extract_json
from trendminer.prompts import Prompt


def as_list(value: Any) -> list:
    """把 LLM 返回结果统一成 list（容忍 dict 包裹、单元素等情况）。"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        if set(value.keys()) == {"items"} and isinstance(value["items"], list):
            return value["items"]
        return list(value.values())
    return [value]


def pick_list(data: Any, key: str) -> list:
    """从阶段返回的 dict 中取指定 key 的列表；若整体就是列表则直接返回。"""
    if isinstance(data, dict):
        return as_list(data.get(key))
    return as_list(data)


def call_stage(
    ctx: PipelineContext,
    llm: Any,
    prompt: Prompt,
    variables: Dict[str, Any],
    *,
    seed: Optional[int] = None,
) -> Any:
    """渲染 prompt -> 调 LLM -> 解析 JSON -> 落盘。resume 时优先复用已有产物。"""
    if ctx.resume and ctx.has_stage(prompt.stage):
        cached = ctx.load_stage(prompt.stage)
        if cached is not None:
            ctx.warnings.append(f"[resume] 复用阶段 {prompt.stage}")
            return cached

    messages = prompt.render(variables)
    started = time.time()
    raw = llm.chat(
        messages,
        stage=prompt.stage,
        temperature=prompt.temperature,
        seed=seed,
    )
    ctx.timings[prompt.stage] = round(time.time() - started, 3)

    data = extract_json(raw)
    ctx.save_stage(prompt.stage, raw, data)
    return data
