"""s5 自动暴露时代性问题。"""
from __future__ import annotations

from typing import Any, List

from trendminer.context import PipelineContext
from trendminer.models import Problem, RetrievalResult, TopicInput
from trendminer.pipeline.base import call_stage, pick_list
from trendminer.pipeline.textfmt import analysis_text, evidence_text, inflections_text, scenarios_text


def run(
    ctx: PipelineContext,
    llm: Any,
    prompts: Any,
    topic_input: TopicInput,
    settings: Any,
) -> List[Problem]:
    prompt = prompts.get("s5_problems")
    retrieval: RetrievalResult = ctx.retrieved or RetrievalResult()
    variables = {
        "topic": topic_input.topic,
        "industry": topic_input.industry,
        "evidence_text": evidence_text([*retrieval.old_era, *retrieval.new_era]),
        "analysis_text": analysis_text(ctx.analysis_frames),
        "scenarios_text": scenarios_text(ctx.scenarios),
        "inflections_text": inflections_text(ctx.inflections),
        "max_problems": settings.max_problems,
    }
    data = call_stage(ctx, llm, prompt, variables)
    problems: List[Problem] = []
    for idx, raw in enumerate(pick_list(data, "problems")):
        problem = Problem.model_validate(raw)
        if not problem.id:
            problem.id = f"P{idx + 1}"
        problems.append(problem)
    problems = problems[: settings.max_problems]
    ctx.problems = problems
    return problems
