"""命令行入口。"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from trendminer.config import load_settings
from trendminer.models import TopicInput
from trendminer.pipeline.orchestrator import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trendminer",
        description="AI时代趋势问题挖掘与变现规划系统",
    )
    parser.add_argument("--topic", required=True, help="主题，如「AI编程」「AI医疗」")
    parser.add_argument("--industry", default="", help="行业/领域")
    parser.add_argument("--horizon", type=int, default=5, help="时间跨度（年），默认 5")
    parser.add_argument("--persona", default="普通职场人", help="目标人群，默认「普通职场人」")
    parser.add_argument("--scenarios", type=int, default=4, help="情景数量，默认 4")
    parser.add_argument("--focus", action="append", default=[], help="关注重点，可重复传入")
    parser.add_argument("--out", default=None, help="输出根目录（默认取 settings.yaml）")
    parser.add_argument("--provider", default=None, help="覆盖 provider（deepseek/qwen/openai）")
    parser.add_argument("--formats", default="md,html", help="输出格式，逗号分隔，默认 md,html")
    parser.add_argument("--seed", type=int, default=0, help="随机推演种子")
    parser.add_argument("--dry-run", action="store_true", help="使用 Mock LLM 离线回放 fixtures")
    parser.add_argument("--resume", action="store_true", help="复用同 run_id 已有阶段产物")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings()
    if args.out:
        settings.output_dir = args.out
    formats = [f.strip() for f in args.formats.split(",") if f.strip()]

    topic_input = TopicInput(
        topic=args.topic,
        industry=args.industry,
        horizon_years=args.horizon,
        persona=args.persona,
        scenario_count=args.scenarios,
        focus=args.focus,
    )

    report = run_pipeline(
        topic_input,
        settings,
        provider=args.provider,
        dry_run=args.dry_run,
        resume=args.resume,
        seed=args.seed,
        formats=formats,
    )

    meta = report.run_meta
    print(f"[trendminer] run_id = {meta.run_id}")
    print(f"[trendminer] provider = {meta.provider}/{meta.model} | dry_run = {meta.dry_run}")
    print(
        f"[trendminer] 产出：关键节点 {len(report.inflections)}｜情景 {len(report.scenarios)}"
        f"｜问题 {len(report.problems)}｜评估 {len(report.evaluations)}"
    )
    print(f"[trendminer] 报告目录：{settings.output_dir}/{meta.run_id}/")
    for fmt in formats:
        print(f"  - report.{fmt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
