"""把结构化对象渲染为注入 prompt 的纯文本块。"""
from __future__ import annotations

from typing import Any, Iterable, List

from trendminer.models import (
    AnalysisFrame,
    Evaluation,
    Evidence,
    InflectionNode,
    Problem,
    Scenario,
    Uncertainty,
)


def _bullets(items: Iterable[str], empty: str = "（无）") -> str:
    lines = [f"- {x}" for x in items if str(x).strip()]
    return "\n".join(lines) if lines else empty


def _join(items: Iterable[str], sep: str = "；", empty: str = "—") -> str:
    values = [str(x) for x in items if str(x).strip()]
    return sep.join(values) if values else empty


def search_results_text(results: List[Any]) -> str:
    if not results:
        return "（无）"
    lines = []
    for r in results:
        src = f"（来源: {r.url}）" if getattr(r, "url", "") else ""
        lines.append(f"- [{r.dimension}] {r.title}{src}\n  {r.content}")
    return "\n".join(lines)


def evidence_text(items: List[Evidence]) -> str:
    if not items:
        return "（无）"
    return "\n".join(
        f"- [{e.code or '—'}][{e.dimension or e.category}] {e.claim}"
        f"（类型: {e.source_type or '先验'}；来源: {e.source_hint or '模型先验'}；"
        f"可信度 {e.credibility}；时效 {e.recency or '未标注'}）"
        for e in items
    )


def analysis_text(items: List[AnalysisFrame]) -> str:
    if not items:
        return "（无）"
    return "\n".join(
        f"- [{f.framework}·{f.dimension}] {'；'.join(f.findings) or '—'}"
        + (f"｜推论: {f.implications}" if f.implications else "")
        for f in items
    )


def inflections_text(items: List[InflectionNode]) -> str:
    if not items:
        return "（无）"
    return "\n".join(
        f"- [{n.node_type}] {n.description}"
        f"｜触发信号: {_join(n.trigger_signals)}"
        f"｜领先指标: {_join(n.leading_indicators)}"
        f"｜前提假设: {_join(n.assumptions)}"
        f"｜时间: {n.eta}｜影响: {n.impact_score}"
        for n in items
    )


def reasoning_text(mode: str, timeline, branches) -> str:
    lines = []
    for h in timeline:
        lines.append(
            f"- [{h.horizon}] {h.statement}"
            f"（驱动: {_join(h.drivers, '、')}；阻碍: {_join(h.blockers, '、')}；"
            f"反方/证伪: {_join(h.counterpoints, '、')}；领先指标: {_join(h.leading_indicators, '、')}；"
            f"确信度 {h.confidence}）"
        )
    if branches:
        lines.append("黑天鹅分支: " + "；".join(branches))
    return f"【{mode}】\n" + ("\n".join(lines) if lines else "（无）")


def uncertainty_text(items: List[Uncertainty]) -> str:
    if not items:
        return "（无）"
    return "\n".join(
        f"- {u.topic}｜分歧: {u.divergence}"
        f"｜可能走向: {_join(u.outcomes, '、')}"
        f"｜监测信号: {_join(u.monitoring_signals, '、')}"
        f"｜影响 {u.impact}／可能 {u.likelihood}"
        for u in items
    )


def scenarios_text(items: List[Scenario]) -> str:
    if not items:
        return "（无）"
    return "\n".join(
        f"- {s.name}（概率 {s.probability:.2f}，生效 {s.effective_time}，破坏 {s.disruption}，红利 {s.dividend_space}）：{s.summary}"
        for s in items
    )


def problems_text(items: List[Problem]) -> str:
    if not items:
        return "（无）"
    return "\n".join(
        f"- {p.id}｜{p.title}｜类别: {p.category}｜严重度 {p.severity}"
        f"｜矛盾: {p.conflict}｜根因: {p.root_cause or '—'}"
        f"｜未解原因: {p.why_unsolved or '—'}｜受影响: {_join(p.affected, '、')}"
        f"｜说明: {p.description}"
        for p in items
    )


def evaluations_text(problems: List[Problem], evaluations: List[Evaluation]) -> str:
    if not problems:
        return "（无）"
    by_id = {e.problem_id: e for e in evaluations}
    lines = []
    for p in problems:
        e = by_id.get(p.id)
        if e:
            method = e.method.summary if e.method and e.method.summary else e.solution_path
            lines.append(
                f"- {p.id}｜{p.title}｜难度 {e.difficulty}｜成本 {e.cost_level}｜紧急度 {e.urgency}"
                f"｜收益 {e.revenue_potential}｜综合分 {e.score:.1f}｜解法: {method or '—'}"
            )
        else:
            lines.append(f"- {p.id}｜{p.title}｜（未评估）")
    return "\n".join(lines)
