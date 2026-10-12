"""把 PipelineReport 渲染为 HTML 报告。"""
from __future__ import annotations

from jinja2 import Environment, FileSystemLoader, select_autoescape

from trendminer.config import TEMPLATES_DIR
from trendminer.models import PipelineReport
from trendminer.render.markdown import _evidence_index, _model_rows


def _stars(value: float) -> str:
    n = int(round(min(5.0, max(1.0, value))))
    return "★" * n + "☆" * (5 - n)


def render_html(report: PipelineReport) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["stars"] = _stars
    template = env.get_template("report.html.j2")

    eval_by_id = {e.problem_id: e for e in report.evaluations}
    ranked_problems = sorted(
        report.problems,
        key=lambda p: eval_by_id[p.id].score if p.id in eval_by_id else p.severity * 20,
        reverse=True,
    )
    return template.render(
        report=report,
        t=report.topic_input,
        meta=report.run_meta,
        problem_title={p.id: p.title for p in report.problems},
        eval_by_id=eval_by_id,
        ranked_problems=ranked_problems,
        model_rows=_model_rows(report),
        evidence_index=_evidence_index(report),
    )
