"""s1 趋势信息检索：多维度信息收集（旧时代存量 + 新时代增量 + 空白/缺口）。"""
from __future__ import annotations

from typing import Any, List

from trendminer.context import PipelineContext
from trendminer.models import RetrievalResult, TopicInput
from trendminer.pipeline.base import call_stage
from trendminer.pipeline.textfmt import search_results_text
from trendminer.search import build_search
from trendminer.search.base import SearchResult


def _gather(backend: Any, topic_input: TopicInput, settings: Any) -> List[SearchResult]:
    cfg = settings.search
    results: List[SearchResult] = []
    for dimension in cfg.dimensions:
        query = f"{topic_input.topic} {dimension}"
        if topic_input.industry:
            query += f" {topic_input.industry}"
        results.extend(backend.search(query, dimension, cfg.max_results_per_dimension))
    return results


def _search_block(backend: Any, topic_input: TopicInput, settings: Any, ctx: PipelineContext):
    """返回 (search_text, search_rule)；检索不可用时降级为模型先验并记录告警。"""
    if not backend.available:
        ctx.warnings.append(f"[检索] {backend.degraded_reason}；所有证据 source_type 标记为「先验」")
        return (
            "（本次未接入实时检索，无外部资料）",
            "本次无外部资料，请完全基于模型先验知识作答，所有 evidence 的 source_type 一律填「先验」，"
            "并在 open_questions 中明确列出需要人工核实的关键信息。",
        )

    results = _gather(backend, topic_input, settings)
    if not results:
        ctx.warnings.append("[检索] 检索后端返回空结果，降级为模型先验；证据 source_type 标记为「先验」")
        return (
            "（检索未返回结果）",
            "检索未返回有效结果，请基于模型先验作答，source_type 一律填「先验」。",
        )

    ctx.warnings.append(f"[检索] 通过 {backend.name} 获取 {len(results)} 条外部资料")
    return (
        search_results_text(results),
        "上方为实时检索资料，优先基于其作答；直接引用检索资料的 evidence，source_type 填「检索」并抄录 source_hint；"
        "仅凭模型记忆补充的填「先验」。请按资料质量给出 credibility。",
    )


def run(
    ctx: PipelineContext,
    llm: Any,
    prompts: Any,
    topic_input: TopicInput,
    settings: Any,
) -> RetrievalResult:
    prompt = prompts.get("s1_retrieval")
    backend = build_search(settings)
    search_text, search_rule = _search_block(backend, topic_input, settings, ctx)

    variables = {
        "topic": topic_input.topic,
        "industry": topic_input.industry,
        "horizon_years": topic_input.horizon_years,
        "focus_text": "、".join(topic_input.focus),
        "max_evidence": settings.max_evidence,
        "search_text": search_text,
        "search_rule": search_rule,
    }
    data = call_stage(ctx, llm, prompt, variables)
    result = RetrievalResult.model_validate(data if isinstance(data, dict) else {})
    result.old_era = result.old_era[: settings.max_evidence]
    result.new_era = result.new_era[: settings.max_evidence]

    if not backend.available:
        for evidence in [*result.old_era, *result.new_era]:
            evidence.source_type = "先验"

    # 统一编号，供后续问题引用溯源（E1、E2…）
    for idx, evidence in enumerate([*result.old_era, *result.new_era], start=1):
        evidence.code = f"E{idx}"

    ctx.retrieved = result
    return result
