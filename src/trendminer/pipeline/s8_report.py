"""s8 报告渲染与落盘。"""
from __future__ import annotations

from pathlib import Path
from typing import List

from trendminer.context import PipelineContext
from trendminer.models import PipelineReport
from trendminer.render.html import render_html
from trendminer.render.markdown import render_markdown


def run(ctx: PipelineContext, report: PipelineReport, formats: List[str]) -> List[Path]:
    written: List[Path] = []
    if "md" in formats:
        path = ctx.run_dir / "report.md"
        path.write_text(render_markdown(report), encoding="utf-8")
        written.append(path)
    if "html" in formats:
        path = ctx.run_dir / "report.html"
        path.write_text(render_html(report), encoding="utf-8")
        written.append(path)
    return written
