"""数据模型：定义各阶段之间流转的结构化对象。

所有模型对 LLM 输出保持宽松兼容（数值/字符串混用、list/dict 混用都能容忍），
避免因模型措辞差异导致校验失败。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

_CONF_MAP = {
    "high": 0.8, "medium": 0.5, "low": 0.2,
    "高": 0.8, "中": 0.5, "低": 0.2, "很高": 0.9, "很低": 0.1,
}


def _to_float(v: Any, default: float = 0.5) -> float:
    if isinstance(v, bool):
        return float(v)
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in _CONF_MAP:
            return _CONF_MAP[s]
        try:
            return float(s.rstrip("星%分"))
        except ValueError:
            return default
    return default


def _to_list(v: Any) -> List[Any]:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        # {"a": {...}, "b": {...}} -> 取 values；{"items": [...]} -> 取 items
        if set(v.keys()) == {"items"} and isinstance(v["items"], list):
            return v["items"]
        return list(v.values())
    return [v]


def _to_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, (int, float, bool)):
        return str(v)
    return str(v)


class Base(BaseModel):
    model_config = ConfigDict(extra="ignore")


# ---------------------------------------------------------------- 输入
class TopicInput(Base):
    topic: str
    industry: str = ""
    horizon_years: int = 5
    persona: str = "普通职场人"
    scenario_count: int = 4
    focus: List[str] = []

    @field_validator("focus", mode="before")
    @classmethod
    def _v_focus(cls, v):
        return [ _to_str(x) for x in _to_list(v) ]

    @field_validator("horizon_years", "scenario_count", mode="before")
    @classmethod
    def _v_int(cls, v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return 5


# ---------------------------------------------------------------- s1 检索
class Evidence(Base):
    code: str = ""              # 证据编号（E1、E2…），供问题引用溯源
    claim: str = ""
    category: str = ""          # 规则/岗位/商业模式/技术/政策/空白
    dimension: str = ""         # 技术/政策/市场/资本/社会/人才
    source_type: str = "先验"    # 检索/先验
    source_hint: str = ""
    credibility: float = 0.5    # 来源可信度 0~1
    recency: str = ""           # 时效性，如「2025年」「长期」
    confidence: float = 0.5

    @field_validator("code", "claim", "category", "dimension", "source_type", "source_hint", "recency", mode="before")
    @classmethod
    def _v_str(cls, v):
        return _to_str(v)

    @field_validator("credibility", "confidence", mode="before")
    @classmethod
    def _v_conf(cls, v):
        return _to_float(v, 0.5)


class RetrievalResult(Base):
    old_era: List[Evidence] = []
    new_era: List[Evidence] = []
    dimensions: List[str] = []      # 本次实际覆盖的维度
    gaps: List[str] = []
    open_questions: List[str] = []  # 未解决的信息缺口

    @field_validator("old_era", "new_era", mode="before")
    @classmethod
    def _v_evidence(cls, v):
        return _to_list(v)

    @field_validator("dimensions", "gaps", "open_questions", mode="before")
    @classmethod
    def _v_gaps(cls, v):
        return [_to_str(x) for x in _to_list(v)]


# ---------------------------------------------------------------- s2b 分析框架
class AnalysisFrame(Base):
    framework: str = ""         # PESTEL/价值链/采用曲线
    dimension: str = ""         # 框架下的具体维度（如 政治/经济/上游/早期采用者）
    findings: List[str] = []
    implications: str = ""      # 对「机会/问题」的推论

    @field_validator("framework", "dimension", "implications", mode="before")
    @classmethod
    def _v_str(cls, v):
        return _to_str(v)

    @field_validator("findings", mode="before")
    @classmethod
    def _v_list(cls, v):
        return [_to_str(x) for x in _to_list(v)]


# ---------------------------------------------------------------- s2 关键节点
class InflectionNode(Base):
    node_type: str = ""         # 技术落地/行业重构/政策变更/用户习惯/商业模式失效新生
    description: str = ""
    trigger_signals: List[str] = []
    leading_indicators: List[str] = []   # 领先指标：先于节点出现的可观测信号
    assumptions: List[str] = []          # 该判断成立所依赖的前提假设
    eta: str = ""               # 预计发生时间
    impact_score: float = 0.5

    @field_validator("node_type", "description", "eta", mode="before")
    @classmethod
    def _v_str(cls, v):
        return _to_str(v)

    @field_validator("trigger_signals", "leading_indicators", "assumptions", mode="before")
    @classmethod
    def _v_list(cls, v):
        return [_to_str(x) for x in _to_list(v)]

    @field_validator("impact_score", mode="before")
    @classmethod
    def _v_score(cls, v):
        return _to_float(v, 0.5)


# ---------------------------------------------------------------- s3 推演
class Hypothesis(Base):
    horizon: str = ""           # 短/中/长
    statement: str = ""
    drivers: List[str] = []
    blockers: List[str] = []
    counterpoints: List[str] = []        # 反方观点/证伪条件
    leading_indicators: List[str] = []   # 可监测的领先指标
    confidence: float = 0.5

    @field_validator("horizon", "statement", mode="before")
    @classmethod
    def _v_str(cls, v):
        return _to_str(v)

    @field_validator("drivers", "blockers", "counterpoints", "leading_indicators", mode="before")
    @classmethod
    def _v_list(cls, v):
        return [_to_str(x) for x in _to_list(v)]

    @field_validator("confidence", mode="before")
    @classmethod
    def _v_conf(cls, v):
        return _to_float(v, 0.5)


class ReasoningOutput(Base):
    mode: str = "linear"        # linear | stochastic
    timeline: List[Hypothesis] = []
    branches: List[str] = []    # 随机推演专有：发散分支
    persona: str = ""
    temperature: float = 0.4
    seed: Optional[int] = None

    @field_validator("timeline", mode="before")
    @classmethod
    def _v_timeline(cls, v):
        return _to_list(v)

    @field_validator("branches", mode="before")
    @classmethod
    def _v_branches(cls, v):
        return [_to_str(x) for x in _to_list(v)]


# ---------------------------------------------------------------- s3c 不确定性
class Uncertainty(Base):
    topic: str = ""                 # 不确定性变量
    divergence: str = ""            # 线性与随机推演在此处的分歧
    outcomes: List[str] = []        # 可能的走向
    monitoring_signals: List[str] = []  # 监测信号（出现即提示走向哪一支）
    impact: float = 0.5             # 影响程度 0~1
    likelihood: float = 0.5         # 发生可能 0~1

    @field_validator("topic", "divergence", mode="before")
    @classmethod
    def _v_str(cls, v):
        return _to_str(v)

    @field_validator("outcomes", "monitoring_signals", mode="before")
    @classmethod
    def _v_list(cls, v):
        return [_to_str(x) for x in _to_list(v)]

    @field_validator("impact", "likelihood", mode="before")
    @classmethod
    def _v_score(cls, v):
        return _to_float(v, 0.5)


# ---------------------------------------------------------------- s4 情景
class Scenario(Base):
    name: str = ""              # 保守/常规/激进/混沌
    probability: float = 0.25
    effective_time: str = ""
    affected_groups: List[str] = []
    affected_industries: List[str] = []
    disruption: float = 3.0     # 1-5
    dividend_space: float = 3.0 # 1-5
    derived_from: str = ""      # linear/stochastic/blend
    summary: str = ""

    @field_validator("name", "effective_time", "derived_from", "summary", mode="before")
    @classmethod
    def _v_str(cls, v):
        return _to_str(v)

    @field_validator("affected_groups", "affected_industries", mode="before")
    @classmethod
    def _v_list(cls, v):
        return [_to_str(x) for x in _to_list(v)]

    @field_validator("probability", mode="before")
    @classmethod
    def _v_prob(cls, v):
        return max(0.0, _to_float(v, 0.25))

    @field_validator("disruption", "dividend_space", mode="before")
    @classmethod
    def _v_15(cls, v):
        return min(5.0, max(1.0, _to_float(v, 3.0)))


# ---------------------------------------------------------------- s5 问题
class Problem(Base):
    id: str = ""
    title: str = ""
    category: str = ""          # 能力错配/工具流程错配/行业空白/个体生存焦虑/企业降本淘汰/AI配套缺失
    description: str = ""
    conflict: str = ""          # 旧 vs 新 的矛盾陈述
    root_cause: str = ""        # 根因：为什么会出现这个矛盾
    why_unsolved: str = ""      # 为什么至今未被解决（阻力/门槛/认知盲区）
    affected: List[str] = []    # 受影响人群/角色
    severity: float = 3.0       # 严重程度 1-5
    derived_models: List[str] = []  # 该问题由哪些分析模型推出（PESTEL/价值链/…）
    evidence_refs: List[str] = []

    @field_validator("id", "title", "category", "description", "conflict", "root_cause", "why_unsolved", mode="before")
    @classmethod
    def _v_str(cls, v):
        return _to_str(v)

    @field_validator("affected", "derived_models", "evidence_refs", mode="before")
    @classmethod
    def _v_list(cls, v):
        return [_to_str(x) for x in _to_list(v)]

    @field_validator("severity", mode="before")
    @classmethod
    def _v_15(cls, v):
        return min(5.0, max(1.0, _to_float(v, 3.0)))


# ---------------------------------------------------------------- s6 方法 + 评估
class SolutionMethod(Base):
    summary: str = ""               # 解法一句话概述
    steps: List[str] = []           # 执行步骤（有序）
    tools: List[str] = []           # 所需工具/资源
    knowledge: List[str] = []       # 所需知识/技能
    milestones: List[str] = []      # 里程碑
    metrics: List[str] = []         # 衡量指标
    pitfalls: List[str] = []        # 避坑点
    mvp: str = ""                   # 最小可行产品/最小可交付
    validation_experiment: str = "" # 验证实验：用最小成本验证需求真伪

    @field_validator("summary", "mvp", "validation_experiment", mode="before")
    @classmethod
    def _v_str(cls, v):
        return _to_str(v)

    @field_validator("steps", "tools", "knowledge", "milestones", "metrics", "pitfalls", mode="before")
    @classmethod
    def _v_list(cls, v):
        return [_to_str(x) for x in _to_list(v)]


class Evaluation(Base):
    problem_id: str = ""
    difficulty: float = 3.0     # 1-5（越高越难）
    cost_level: str = "中"      # 低/中/高
    cost_estimate: str = ""
    urgency: float = 3.0        # 1-5
    revenue_potential: float = 3.0  # 1-5
    solution_path: str = ""
    method: Optional[SolutionMethod] = None   # 结构化解法
    score: float = 0.0

    @field_validator("problem_id", "cost_level", "cost_estimate", "solution_path", mode="before")
    @classmethod
    def _v_str(cls, v):
        return _to_str(v)

    @field_validator("difficulty", "urgency", "revenue_potential", mode="before")
    @classmethod
    def _v_15(cls, v):
        return min(5.0, max(1.0, _to_float(v, 3.0)))

    @field_validator("method", mode="before")
    @classmethod
    def _v_method(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return {"summary": v} if v.strip() else None
        if isinstance(v, dict):
            return v or None
        return None


# ---------------------------------------------------------------- s7 规划
class Monetization(Base):
    model: str = ""             # 服务/课程/工具/SaaS/咨询
    pricing: str = ""
    first_100_customers: str = ""
    milestone: str = ""
    related_problem_ids: List[str] = []

    @field_validator("model", "pricing", "first_100_customers", "milestone", mode="before")
    @classmethod
    def _v_str(cls, v):
        return _to_str(v)

    @field_validator("related_problem_ids", mode="before")
    @classmethod
    def _v_list(cls, v):
        return [_to_str(x) for x in _to_list(v)]


class RoadmapPhase(Base):
    window: str = ""            # 0-30天 / 31-60天 / 61-90天
    goal: str = ""
    tasks: List[str] = []
    metrics: List[str] = []

    @field_validator("window", "goal", mode="before")
    @classmethod
    def _v_str(cls, v):
        return _to_str(v)

    @field_validator("tasks", "metrics", mode="before")
    @classmethod
    def _v_list(cls, v):
        return [_to_str(x) for x in _to_list(v)]


class Plan(Base):
    capability_fit: Dict[str, Any] = {}
    roadmap_30_60_90: List[RoadmapPhase] = []   # 90 天落地路线图
    short_term_tasks: List[str] = []
    mid_long_positioning: List[str] = []
    monetization_paths: List[Monetization] = []
    learning_loop: List[str] = []
    risks: List[str] = []

    @field_validator("capability_fit", mode="before")
    @classmethod
    def _v_fit(cls, v):
        return v if isinstance(v, dict) else {"summary": _to_str(v)}

    @field_validator("short_term_tasks", "mid_long_positioning", "learning_loop", "risks", mode="before")
    @classmethod
    def _v_list(cls, v):
        return [_to_str(x) for x in _to_list(v)]

    @field_validator("monetization_paths", "roadmap_30_60_90", mode="before")
    @classmethod
    def _v_monetization(cls, v):
        return _to_list(v)


# ---------------------------------------------------------------- 汇总
class RunMeta(Base):
    run_id: str = ""
    provider: str = ""
    model: str = ""
    seed: Optional[int] = None
    dry_run: bool = False
    timings: Dict[str, float] = {}
    warnings: List[str] = []


class PipelineReport(Base):
    topic_input: TopicInput
    retrieved: Optional[RetrievalResult] = None
    analysis_frames: List[AnalysisFrame] = []
    inflections: List[InflectionNode] = []
    linear: Optional[ReasoningOutput] = None
    stochastic: Optional[ReasoningOutput] = None
    uncertainties: List[Uncertainty] = []
    scenarios: List[Scenario] = []
    problems: List[Problem] = []
    evaluations: List[Evaluation] = []
    plan: Optional[Plan] = None
    run_meta: RunMeta = RunMeta()
