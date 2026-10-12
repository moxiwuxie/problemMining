"""s2 关键节点拆解：定位时代拐点。"""
from __future__ import annotations

from typing import Any, List

from trendminer.context import PipelineContext
from trendminer.models import InflectionNode, RetrievalResult, TopicInput
from trendminer.pipeline.base import call_stage, pick_list
from trendminer.pipeline.textfmt import _bullets, evidence_text


def run(
    ctx: PipelineContext,
    llm: Any,
    prompts: Any,
    topic_input: TopicInput,
    settings: Any,
) -> List[InflectionNode]:
    prompt = prompts.get("s2_inflection")
    retrieval: RetrievalResult = ctx.retrieved or RetrievalResult()
    variables = {
        "topic": topic_input.topic,
        "industry": topic_input.industry,
        "horizon_years": topic_input.horizon_years,
        "old_era_text": evidence_text(retrieval.old_era),
        "new_era_text": evidence_text(retrieval.new_era),
        "gaps_text": _bullets(retrieval.gaps),
        "max_inflections": settings.max_inflections,
    }
    data = call_stage(ctx, llm, prompt, variables)
    nodes = [InflectionNode.model_validate(n) for n in pick_list(data, "nodes")]
    nodes = nodes[: settings.max_inflections]
    ctx.inflections = nodes
    return nodes
