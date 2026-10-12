"""s3b 随机推演：混沌变量（引入 persona 与 seed 保证发散）。"""
from __future__ import annotations

import random
from typing import Any

from trendminer.context import PipelineContext
from trendminer.models import Hypothesis, ReasoningOutput, TopicInput
from trendminer.pipeline.base import call_stage, pick_list, as_list
from trendminer.pipeline.textfmt import inflections_text

PERSONAS = ["末日论者", "技术乐观派", "资本视角", "监管视角"]


def run(
    ctx: PipelineContext,
    llm: Any,
    prompts: Any,
    topic_input: TopicInput,
    *,
    seed: int = 0,
) -> ReasoningOutput:
    prompt = prompts.get("s3b_stochastic")
    rng = random.Random(seed)
    persona = rng.choice(PERSONAS)
    variables = {
        "topic": topic_input.topic,
        "industry": topic_input.industry,
        "horizon_years": topic_input.horizon_years,
        "inflections_text": inflections_text(ctx.inflections),
        "persona": persona,
        "seed": seed,
    }
    data = call_stage(ctx, llm, prompt, variables, seed=seed)
    timeline = [Hypothesis.model_validate(h) for h in pick_list(data, "timeline")]
    branches = [str(b) for b in (data.get("branches", []) if isinstance(data, dict) else as_list(data))]
    output = ReasoningOutput(
        mode="stochastic",
        timeline=timeline,
        branches=branches,
        persona=persona,
        temperature=prompt.temperature,
        seed=seed,
    )
    ctx.stochastic = output
    return output
