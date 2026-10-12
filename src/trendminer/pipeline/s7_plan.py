"""s7 变现工程规划。"""
from __future__ import annotations

from typing import Any

from trendminer.context import PipelineContext
from trendminer.models import Plan, TopicInput
from trendminer.pipeline.base import call_stage
from trendminer.pipeline.textfmt import evaluations_text


def run(ctx: PipelineContext, llm: Any, prompts: Any, topic_input: TopicInput) -> Plan:
    prompt = prompts.get("s7_plan")
    variables = {
        "topic": topic_input.topic,
        "persona": topic_input.persona,
        "evaluations_text": evaluations_text(ctx.problems, ctx.evaluations),
    }
    data = call_stage(ctx, llm, prompt, variables)
    plan = Plan.model_validate(data if isinstance(data, dict) else {})
    # 按综合分排序，便于报告呈现优先级
    ctx.evaluations = sorted(ctx.evaluations, key=lambda e: e.score, reverse=True)
    ctx.plan = plan
    return plan
