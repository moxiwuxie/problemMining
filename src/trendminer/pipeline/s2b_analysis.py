"""s2b 结构化分析：用 PESTEL / 价值链 / 采用曲线 压缩信息为可判断结构。"""
from __future__ import annotations

from typing import Any, List

from trendminer.context import PipelineContext
from trendminer.models import AnalysisFrame, RetrievalResult, TopicInput
from trendminer.pipeline.base import call_stage, pick_list
from trendminer.pipeline.textfmt import _bullets, evidence_text


def run(
    ctx: PipelineContext,
    llm: Any,
    prompts: Any,
    topic_input: TopicInput,
    settings: Any = None,
) -> List[AnalysisFrame]:
    prompt = prompts.get("s2b_analysis")
    retrieval: RetrievalResult = ctx.retrieved or RetrievalResult()
    variables = {
        "topic": topic_input.topic,
        "industry": topic_input.industry,
        "horizon_years": topic_input.horizon_years,
        "dimensions_text": _bullets(retrieval.dimensions),
        "old_era_text": evidence_text(retrieval.old_era),
        "new_era_text": evidence_text(retrieval.new_era),
        "gaps_text": _bullets(retrieval.gaps),
    }
    data = call_stage(ctx, llm, prompt, variables)
    frames = [AnalysisFrame.model_validate(x) for x in pick_list(data, "frames")]
    ctx.analysis_frames = frames
    return frames
