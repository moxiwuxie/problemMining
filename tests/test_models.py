from trendminer.models import (
    Evaluation,
    Evidence,
    Plan,
    Problem,
    RetrievalResult,
    Scenario,
    SolutionMethod,
    TopicInput,
    Uncertainty,
)
from trendminer.pipeline.s6_evaluation import compute_score


def test_topic_input_coerces_types():
    t = TopicInput(topic="AI", horizon_years="7", focus="单点")
    assert t.horizon_years == 7
    assert t.focus == ["单点"]


def test_evidence_accepts_dict_and_str_confidence():
    r = RetrievalResult.model_validate(
        {"old_era": {"a": {"claim": "x", "confidence": "high"}}, "gaps": "单条"}
    )
    assert isinstance(r.old_era[0], Evidence)
    assert r.old_era[0].confidence == 0.8
    assert r.gaps == ["单条"]


def test_scenario_clamps_ranges():
    s = Scenario.model_validate({"name": "激进", "probability": -1, "disruption": 9})
    assert s.probability == 0.0
    assert s.disruption == 5.0


def test_compute_score_prefers_easy_cheap_high_value():
    weights = {"difficulty": 0.25, "urgency": 0.25, "revenue_potential": 0.35, "cost": 0.15}
    good = Evaluation(problem_id="P1", difficulty=1, cost_level="低", urgency=5, revenue_potential=5)
    bad = Evaluation(problem_id="P2", difficulty=5, cost_level="高", urgency=1, revenue_potential=1)
    assert compute_score(good, weights) > compute_score(bad, weights)
    assert compute_score(good, weights) == 100.0
    assert compute_score(bad, weights) == 0.0


def test_evidence_new_fields_have_safe_defaults():
    e = Evidence(claim="x")
    assert e.dimension == ""
    assert e.source_type == "先验"
    assert e.credibility == 0.5
    assert e.recency == ""


def test_retrieval_result_carries_dimensions_and_gaps():
    r = RetrievalResult.model_validate(
        {"dimensions": "技术", "open_questions": {"q": "缺什么"}, "gaps": []}
    )
    assert r.dimensions == ["技术"]
    assert r.open_questions == ["缺什么"]


def test_problem_severity_clamped_and_defaults():
    p = Problem.model_validate({"id": "P1", "severity": 9})
    assert p.severity == 5.0
    assert p.root_cause == ""
    assert p.affected == []
    assert p.derived_models == []


def test_problem_accepts_derived_models_and_evidence_codes():
    p = Problem.model_validate(
        {"id": "P1", "derived_models": "PESTEL", "evidence_refs": ["E1", "E3"]}
    )
    assert p.derived_models == ["PESTEL"]
    assert p.evidence_refs == ["E1", "E3"]


def test_evaluation_accepts_string_or_dict_method():
    from_str = Evaluation.model_validate({"problem_id": "P1", "method": "先服务后产品"})
    assert isinstance(from_str.method, SolutionMethod)
    assert from_str.method.summary == "先服务后产品"

    from_dict = Evaluation.model_validate({"problem_id": "P2", "method": {"steps": ["a"]}})
    assert from_dict.method.steps == ["a"]

    assert Evaluation(problem_id="P3").method is None


def test_plan_parses_roadmap_phases():
    plan = Plan.model_validate(
        {"roadmap_30_60_90": [{"window": "0-30天", "goal": "验证", "tasks": "发问卷", "metrics": ["意向>=3"]}]}
    )
    assert len(plan.roadmap_30_60_90) == 1
    phase = plan.roadmap_30_60_90[0]
    assert phase.tasks == ["发问卷"]
    assert phase.metrics == ["意向>=3"]


def test_uncertainty_accepts_scalar_lists():
    u = Uncertainty.model_validate({"topic": "监管强度", "monitoring_signals": "征求意见稿", "impact": "high"})
    assert u.monitoring_signals == ["征求意见稿"]
    assert u.impact == 0.8
