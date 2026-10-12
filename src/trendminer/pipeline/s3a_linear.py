"""s3a 线性推演：确定性趋势。"""
from __future__ import annotations

from typing import Any

from trendminer.context import PipelineContext
from trendminer.models import Hypothesis, ReasoningOutput, TopicInput
from trendminer.pipeline.base import call_stage, pick_list
from trendminer.pipeline.textfmt import inflections_text


def run(ctx: PipelineContext, llm: Any, prompts: Any, topic_input: TopicInput) -> ReasoningOutput:
    prompt = prompts.get("s3a_linear")
    variables = {
        "topic": topic_input.topic,
        "industry": topic_input.industry,
        "horizon_years": topic_input.horizon_years,
        "inflections_text": inflections_text(ctx.inflections),
    }
    data = call_stage(ctx, llm, prompt, variables)
    timeline = [Hypothesis.model_validate(h) for h in pick_list(data, "timeline")]
    output = ReasoningOutput(
        mode="linear",
        timeline=timeline,
        branches=[],
        temperature=prompt.temperature,
    )
    ctx.linear = output
    return output
