"""PipelineContext：贯穿各阶段的结果容器，负责分阶段落盘与 resume。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class PipelineContext:
    def __init__(self, run_id: str, output_root: Path, *, dry_run: bool = False, resume: bool = False):
        self.run_id = run_id
        self.run_dir = Path(output_root) / run_id
        self.dry_run = dry_run
        self.resume = resume
        self.timings: Dict[str, float] = {}
        self.warnings: List[str] = []

        # 各阶段结构化结果
        self.retrieved: Any = None
        self.analysis_frames: List[Any] = []
        self.inflections: List[Any] = []
        self.linear: Any = None
        self.stochastic: Any = None
        self.uncertainties: List[Any] = []
        self.scenarios: List[Any] = []
        self.problems: List[Any] = []
        self.evaluations: List[Any] = []
        self.plan: Any = None

        self.run_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------- 落盘
    def _stage_path(self, stage: str) -> Path:
        return self.run_dir / f"stage_{stage}.json"

    def has_stage(self, stage: str) -> bool:
        return self._stage_path(stage).exists()

    def save_stage(self, stage: str, raw: str, parsed: Any) -> None:
        payload = {"stage": stage, "raw": raw, "parsed": parsed}
        self._stage_path(stage).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def load_stage(self, stage: str) -> Optional[Any]:
        path = self._stage_path(stage)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("parsed")
        except (json.JSONDecodeError, OSError):
            return None
