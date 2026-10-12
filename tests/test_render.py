from trendminer.pipeline.orchestrator import run_pipeline
from trendminer.render.html import render_html
from trendminer.render.markdown import render_markdown


def _report(settings, sample_topic):
    return run_pipeline(sample_topic, settings, dry_run=True, formats=["md"])


def test_markdown_has_all_sections(settings, sample_topic):
    md = render_markdown(_report(settings, sample_topic))
    for heading in ["核心问题抛出", "分析模型总览", "趋势信息检索", "结构化分析框架", "关键节点拆解",
                    "双模式推演", "关键不确定性与监测信号", "未来情景与概率", "时代性问题清单",
                    "五维量化评估与结构化解法", "变现工程规划", "风险规避", "信息源清单"]:
        assert heading in md
    assert "AI编程" in md
    assert "90 天落地路线图" in md
    assert "根因" in md
    assert "验证实验" in md
    # 信息源标注：证据编号可溯源
    assert "| E1 |" in md
    assert "问题 ← 分析模型 映射" in md


def test_html_has_structure(settings, sample_topic):
    html = render_html(_report(settings, sample_topic))
    assert html.startswith("<!DOCTYPE html>")
    assert "变现工程规划" in html
    assert "五维量化评估" in html
    assert "结构化分析框架" in html
    assert "关键不确定性与监测信号" in html
    assert "90 天落地路线图" in html
    assert "核心问题抛出" in html
    assert "分析模型总览" in html
    assert "信息源清单" in html
