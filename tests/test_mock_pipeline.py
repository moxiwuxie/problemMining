from pathlib import Path

from trendminer.models import PipelineReport
from trendminer.pipeline.orchestrator import run_pipeline


def _run(settings, sample_topic) -> PipelineReport:
    return run_pipeline(
        sample_topic,
        settings,
        dry_run=True,
        seed=11,
        formats=["md", "html"],
    )


def test_pipeline_end_to_end_offline(settings, sample_topic):
    report = _run(settings, sample_topic)

    assert report.run_meta.dry_run is True
    assert report.retrieved is not None
    assert report.retrieved.dimensions, "应标注覆盖的信息维度"
    assert report.retrieved.open_questions, "应给出信息缺口"
    assert all(e.code for e in [*report.retrieved.old_era, *report.retrieved.new_era]), "证据应被编号"
    assert report.analysis_frames, "应有结构化分析框架"
    assert report.inflections, "应有关键节点"
    assert report.linear and report.linear.timeline, "应有线性推演"
    assert report.stochastic and report.stochastic.branches, "随机推演应有黑天鹅分支"
    assert report.uncertainties, "应有不确定性与监测信号"

    # 情景概率归一化
    total = sum(s.probability for s in report.scenarios)
    assert abs(total - 1.0) < 1e-6

    # 问题 -> 评估 引用一致
    problem_ids = {p.id for p in report.problems}
    eval_ids = {e.problem_id for e in report.evaluations}
    assert problem_ids, "应有问题"
    assert eval_ids == problem_ids, "每个问题都应被评估"
    assert all(p.root_cause and p.why_unsolved for p in report.problems), "问题应含根因与未解原因"
    assert all(p.derived_models for p in report.problems), "问题应外显所依据的分析模型"
    assert all(p.evidence_refs for p in report.problems), "问题应引用信息源编号"
    assert all(e.method and e.method.steps for e in report.evaluations), "每个问题都应有结构化解法"

    # 评估按综合分降序
    scores = [e.score for e in report.evaluations]
    assert scores == sorted(scores, reverse=True)

    # 规划存在
    assert report.plan is not None
    assert report.plan.monetization_paths
    assert len(report.plan.roadmap_30_60_90) == 3, "应有 30/60/90 天路线图"


def test_report_files_written(settings, sample_topic):
    report = _run(settings, sample_topic)
    run_dir = Path(settings.output_dir) / report.run_meta.run_id

    assert (run_dir / "report.md").exists()
    assert (run_dir / "report.html").exists()
    # 10 个阶段产物
    for stage in [
        "s1_retrieval", "s2_inflection", "s2b_analysis", "s3a_linear", "s3b_stochastic",
        "s3c_uncertainty", "s4_scenario", "s5_problems", "s6_evaluation", "s7_plan",
    ]:
        assert (run_dir / f"stage_{stage}.json").exists(), stage


def test_resume_reuses_cached_stages(settings, sample_topic):
    first = _run(settings, sample_topic)
    run_id = first.run_meta.run_id

    # 用相同 run_id 触发 resume：monkeypatch 掉 run_id 生成，直接校验 warnings 机制
    from trendminer.context import PipelineContext

    ctx = PipelineContext(run_id, Path(settings.output_dir), resume=True)
    assert ctx.has_stage("s1_retrieval")
    assert ctx.load_stage("s1_retrieval")["old_era"]
