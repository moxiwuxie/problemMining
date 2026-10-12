"""s3c 关键不确定性：校验线性/随机一致性，抽出分歧点与监测信号。"""
from __future__ import annotations

from typing import Any, List

from trendminer.context import PipelineContext
from trendminer.models import TopicInput, Uncertainty
from trendminer.pipeline.base import call_stage, pick_list
from trendminer.pipeline.textfmt import reasoning_text

MAX_UNCERTAINTIES = 5


def run(ctx: PipelineContext, llm: Any, prompts: Any, topic_input: TopicInput) -> List[Uncertainty]:
    prompt = prompts.get("s3c_uncertainty")
    lin = ctx.linear
    sto = ctx.stochastic
    variables = {
        "topic": topic_input.topic,
        "horizon_years": topic_input.horizon_years,
        "linear_text": reasoning_text("线性推演", lin.timeline, []) if lin else "（无）",
        "stochastic_text": reasoning_text("随机推演", sto.timeline, sto.branches) if sto else "（无）",
    }
    data = call_stage(ctx, llm, prompt, variables)
    items = [Uncertainty.model_validate(x) for x in pick_list(data, "uncertainties")]
    items = items[:MAX_UNCERTAINTIES]
    ctx.uncertainties = items
    return items
