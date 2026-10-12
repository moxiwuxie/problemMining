"""s4 未来情景生成 + 概率归一化。"""
from __future__ import annotations

from typing import Any, List

from trendminer.context import PipelineContext
from trendminer.models import Scenario, TopicInput
from trendminer.pipeline.base import call_stage, pick_list
from trendminer.pipeline.textfmt import reasoning_text


def _normalize_probabilities(scenarios: List[Scenario]) -> None:
    total = sum(s.probability for s in scenarios)
    if total <= 0:
        even = round(1.0 / len(scenarios), 4) if scenarios else 0.0
        for s in scenarios:
            s.probability = even
        return
    for s in scenarios:
        s.probability = round(s.probability / total, 4)


def run(ctx: PipelineContext, llm: Any, prompts: Any, topic_input: TopicInput) -> List[Scenario]:
    prompt = prompts.get("s4_scenario")
    lin = ctx.linear
    sto = ctx.stochastic
    variables = {
        "topic": topic_input.topic,
        "horizon_years": topic_input.horizon_years,
        "scenario_count": topic_input.scenario_count,
        "linear_text": reasoning_text("线性推演", lin.timeline, []) if lin else "（无）",
        "stochastic_text": reasoning_text("随机推演", sto.timeline, sto.branches) if sto else "（无）",
    }
    data = call_stage(ctx, llm, prompt, variables)
    scenarios = [Scenario.model_validate(s) for s in pick_list(data, "scenarios")]
    scenarios = scenarios[: topic_input.scenario_count] or scenarios
    _normalize_probabilities(scenarios)
    ctx.scenarios = scenarios
    return scenarios
