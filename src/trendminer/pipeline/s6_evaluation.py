"""s6 五维量化评估 + 综合评分。"""
from __future__ import annotations

from typing import Any, Dict, List

from trendminer.context import PipelineContext
from trendminer.models import Evaluation, TopicInput
from trendminer.pipeline.base import call_stage, pick_list
from trendminer.pipeline.textfmt import problems_text

_COST_SCORE = {"低": 1.0, "中": 0.5, "高": 0.0, "low": 1.0, "medium": 0.5, "high": 0.0}


def compute_score(evaluation: Evaluation, weights: Dict[str, float]) -> float:
    """把五维归一化到 0~1 后加权，输出 0~100 的综合分。"""
    difficulty = (5.0 - evaluation.difficulty) / 4.0        # 越易越高
    urgency = (evaluation.urgency - 1.0) / 4.0
    revenue = (evaluation.revenue_potential - 1.0) / 4.0
    cost = _COST_SCORE.get(str(evaluation.cost_level).strip(), 0.5)
    total = (
        weights.get("difficulty", 0.25) * difficulty
        + weights.get("urgency", 0.25) * urgency
        + weights.get("revenue_potential", 0.35) * revenue
        + weights.get("cost", 0.15) * cost
    )
    return round(total * 100, 1)


def run(
    ctx: PipelineContext,
    llm: Any,
    prompts: Any,
    topic_input: TopicInput,
    settings: Any,
) -> List[Evaluation]:
    prompt = prompts.get("s6_evaluation")
    variables = {
        "topic": topic_input.topic,
        "problems_text": problems_text(ctx.problems),
    }
    data = call_stage(ctx, llm, prompt, variables)
    evaluations: List[Evaluation] = []
    for idx, raw in enumerate(pick_list(data, "evaluations")):
        evaluation = Evaluation.model_validate(raw)
        if not evaluation.problem_id and idx < len(ctx.problems):
            evaluation.problem_id = ctx.problems[idx].id
        evaluation.score = compute_score(evaluation, settings.score_weights)
        evaluations.append(evaluation)
    ctx.evaluations = evaluations
    return evaluations
