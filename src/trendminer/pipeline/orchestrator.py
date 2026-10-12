"""编排器：串联 8 个阶段，产出 PipelineReport。"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from trendminer.config import PROJECT_ROOT, Settings, resolve_provider
from trendminer.context import PipelineContext
from trendminer.llm.client import LLMClient
from trendminer.llm.mock import MockLLMClient
from trendminer.models import PipelineReport, RunMeta, TopicInput
from trendminer.pipeline import (
    s1_retrieval,
    s2_inflection,
    s2b_analysis,
    s3a_linear,
    s3b_stochastic,
    s3c_uncertainty,
    s4_scenario,
    s5_problems,
    s6_evaluation,
    s7_plan,
    s8_report,
)
from trendminer.prompts import PromptLoader


def _make_run_id(topic: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", topic).strip("-")[:20] or "run"
    return f"{ts}_{slug}"


def _resolve_output_root(settings: Settings) -> Path:
    root = Path(settings.output_dir)
    return root if root.is_absolute() else PROJECT_ROOT / root


def run_pipeline(
    topic_input: TopicInput,
    settings: Optional[Settings] = None,
    *,
    provider: Optional[str] = None,
    dry_run: bool = False,
    resume: bool = False,
    seed: int = 0,
    formats: Optional[List[str]] = None,
) -> PipelineReport:
    settings = settings or Settings()
    formats = formats or ["md", "html"]

    provider_name, provider_cfg = resolve_provider(settings, provider)
    if dry_run:
        llm = MockLLMClient(settings, seed=seed)
        model = f"mock:{provider_cfg.model}"
    else:
        llm = LLMClient(provider_cfg, settings)
        model = provider_cfg.model

    prompts = PromptLoader()
    run_id = _make_run_id(topic_input.topic)
    output_root = _resolve_output_root(settings)
    ctx = PipelineContext(run_id, output_root, dry_run=dry_run, resume=resume)

    # s1 检索 -> s2 关键节点 -> s2b 结构化分析
    s1_retrieval.run(ctx, llm, prompts, topic_input, settings)
    s2_inflection.run(ctx, llm, prompts, topic_input, settings)
    s2b_analysis.run(ctx, llm, prompts, topic_input, settings)

    # s3a 线性 + s3b 随机（无依赖，并发）
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_linear = pool.submit(s3a_linear.run, ctx, llm, prompts, topic_input)
        f_stoch = pool.submit(s3b_stochastic.run, ctx, llm, prompts, topic_input, seed=seed)
        f_linear.result()
        f_stoch.result()

    # s3c 不确定性（依赖双推演结果）-> s4 情景 -> s5 问题 -> s6 评估 -> s7 规划
    s3c_uncertainty.run(ctx, llm, prompts, topic_input)
    s4_scenario.run(ctx, llm, prompts, topic_input)
    s5_problems.run(ctx, llm, prompts, topic_input, settings)
    s6_evaluation.run(ctx, llm, prompts, topic_input, settings)
    s7_plan.run(ctx, llm, prompts, topic_input)

    report = PipelineReport(
        topic_input=topic_input,
        retrieved=ctx.retrieved,
        analysis_frames=ctx.analysis_frames,
        inflections=ctx.inflections,
        linear=ctx.linear,
        stochastic=ctx.stochastic,
        uncertainties=ctx.uncertainties,
        scenarios=ctx.scenarios,
        problems=ctx.problems,
        evaluations=ctx.evaluations,
        plan=ctx.plan,
        run_meta=RunMeta(
            run_id=run_id,
            provider=provider_name,
            model=model,
            seed=seed,
            dry_run=dry_run,
            timings=dict(ctx.timings),
            warnings=list(ctx.warnings),
        ),
    )

    s8_report.run(ctx, report, formats)
    report.run_meta.warnings = list(ctx.warnings)
    return report
