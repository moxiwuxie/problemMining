"""把 PipelineReport 渲染为 Markdown 报告。"""
from __future__ import annotations

from trendminer.models import PipelineReport


def _stars(value: float) -> str:
    n = int(round(min(5.0, max(1.0, value))))
    return "★" * n + "☆" * (5 - n)


def _join(items, sep: str = "；", empty: str = "—") -> str:
    values = [str(x) for x in items if str(x).strip()]
    return sep.join(values) if values else empty


def _evidence_index(report: PipelineReport) -> list:
    if not report.retrieved:
        return []
    return [*report.retrieved.old_era, *report.retrieved.new_era]


def _model_rows(report: PipelineReport) -> list:
    """分析模型外显：模型 -> 作用 -> 本次产出。"""
    rows: list = []
    r = report.retrieved
    if r:
        rows.append(("六维信息检索", "按技术/政策/市场/资本/社会/人才多维收集并标注来源",
                     f"覆盖 {'、'.join(r.dimensions) or '未标注'}；证据 {len(_evidence_index(report))} 条；"
                     f"信息缺口 {len(r.open_questions)} 项"))

    grouped: dict = {}
    for f in report.analysis_frames:
        grouped.setdefault(f.framework or "其他", []).append(f)
    framework_role = {
        "PESTEL": "宏观环境扫描，识别外部驱动力与约束",
        "价值链": "拆解上下游，定位被 AI 重构的环节",
        "采用曲线": "判断技术扩散阶段与窗口期",
    }
    for name, frames in grouped.items():
        implications = sum(1 for f in frames if f.implications)
        rows.append((name, framework_role.get(name, "结构化分析"),
                     f"{len(frames)} 个维度分析，{implications} 条推论"))

    if report.linear:
        rows.append(("线性推演", "推演大概率必然发生的确定性趋势",
                     f"{len(report.linear.timeline)} 条假设（含证伪条件与领先指标）"))
    if report.stochastic:
        rows.append(("随机推演", "以混沌视角引入黑天鹅变量",
                     f"{len(report.stochastic.timeline)} 条假设 + {len(report.stochastic.branches)} 条黑天鹅分支"))
    if report.uncertainties:
        rows.append(("不确定性审计", "校验双推演一致性，输出分歧点与监测信号",
                     f"{len(report.uncertainties)} 项不确定性"))
    if report.evaluations:
        methods = sum(1 for e in report.evaluations if e.method)
        rows.append(("五维量化评估", "难度/成本/紧急度/收益/路径标准化打分",
                     f"{len(report.evaluations)} 个问题评分"))
        rows.append(("结构化解法设计", "把问题转化为可执行步骤、MVP 与验证实验",
                     f"{methods} 套解法"))
    return rows


def render_markdown(report: PipelineReport) -> str:
    t = report.topic_input
    meta = report.run_meta
    lines: list[str] = []
    add = lines.append

    add(f"# AI时代趋势问题挖掘与变现规划报告：{t.topic}")
    add("")
    add(f"- 行业/领域：{t.industry or '不限'}")
    add(f"- 时间跨度：未来 {t.horizon_years} 年")
    add(f"- 目标人群：{t.persona}")
    add(f"- 运行：run_id={meta.run_id}｜provider={meta.provider}/{meta.model}｜dry_run={meta.dry_run}")
    add("")
    add("> 核心价值观：所有时代更替的痛点，都是普通人的变现机会。")
    add("")

    eval_by_id = {e.problem_id: e for e in report.evaluations}

    # 摘要：核心问题抛出
    add("## 摘要：核心问题抛出")
    add("")
    if report.problems:
        ranked = sorted(
            report.problems,
            key=lambda p: eval_by_id[p.id].score if p.id in eval_by_id else p.severity * 20,
            reverse=True,
        )
        for i, p in enumerate(ranked, start=1):
            e = eval_by_id.get(p.id)
            metric = f"严重度 {_stars(p.severity)}"
            if e:
                metric += f"｜综合分 {e.score}"
            add(f"{i}. **{p.id} {p.title}**（{metric}）")
            add(f"   - 矛盾：{p.conflict or '—'}")
            add(f"   - 受影响：{_join(p.affected, '、')}｜分析模型：{_join(p.derived_models, '、')}")
        add("")

    # 一、分析模型总览（外显）
    add("## 一、分析模型总览（外显）")
    add("")
    add("> 本节显性列出本报告使用了哪些分析模型、各自产出什么，便于追溯与质疑每一个结论。")
    add("")
    add("| 分析模型 | 作用 | 本次产出 |")
    add("| --- | --- | --- |")
    for name, role, output in _model_rows(report):
        add(f"| {name} | {role} | {output} |")
    add("")
    if report.problems:
        add("**问题 ← 分析模型 映射**")
        add("")
        for p in report.problems:
            add(f"- {p.id} ← {_join(p.derived_models, '、')}")
        add("")

    # 二、信息检索
    add("## 二、趋势信息检索（多维信息收集）")
    add("")
    if report.retrieved:
        r = report.retrieved
        add(f"覆盖维度：{_join(r.dimensions, '、', '未标注')}")
        add("")

        def _evidence_block(title: str, items) -> None:
            add(f"### {title}")
            add("")
            add("| 编号 | 维度 | 类型 | 断言 | 来源 | 可信度 | 时效 |")
            add("| --- | --- | --- | --- | --- | --- | --- |")
            for e in items:
                add(
                    f"| {e.code or '—'} | {e.dimension or e.category or '—'} | {e.source_type or '先验'} | "
                    f"{e.claim} | {e.source_hint or '模型先验'} | {e.credibility} | {e.recency or '—'} |"
                )
            add("")

        _evidence_block("旧时代存量信息", r.old_era)
        _evidence_block("新时代增量信息", r.new_era)

        add("### 空白 / 断层点")
        add("")
        for g in r.gaps:
            add(f"- {g}")
        add("")
        if r.open_questions:
            add("### 信息缺口（待核实）")
            add("")
            for q in r.open_questions:
                add(f"- {q}")
            add("")

    # 三、分析框架
    add("## 三、结构化分析框架（PESTEL / 价值链 / 采用曲线）")
    add("")
    if report.analysis_frames:
        current = None
        for f in report.analysis_frames:
            if f.framework != current:
                if current is not None:
                    add("")
                current = f.framework
                add(f"### {f.framework or '其他'}")
                add("")
            add(f"- **{f.dimension}**")
            for finding in f.findings:
                add(f"  - {finding}")
            if f.implications:
                add(f"  - _推论_：{f.implications}")
        add("")

    # 四、关键节点
    add("## 四、关键节点拆解（时代拐点）")
    add("")
    for n in report.inflections:
        add(f"- **[{n.node_type}]** {n.description}")
        add(f"  - 触发信号：{_join(n.trigger_signals)}")
        add(f"  - 领先指标：{_join(n.leading_indicators)}")
        add(f"  - 前提假设：{_join(n.assumptions)}")
        add(f"  - 预计时间：{n.eta}｜影响强度：{n.impact_score}")
    add("")

    # 五、双模式推演
    add("## 五、双模式推演")

    def _timeline(items) -> None:
        for h in items:
            add(f"- **[{h.horizon}]** {h.statement}")
            add(f"  - 驱动：{_join(h.drivers, '、')}｜阻碍：{_join(h.blockers, '、')}｜确信度：{h.confidence}")
            if h.counterpoints:
                add(f"  - 反方/证伪：{_join(h.counterpoints, '、')}")
            if h.leading_indicators:
                add(f"  - 领先指标：{_join(h.leading_indicators, '、')}")

    add("")
    add("### 5.1 线性推演（确定性趋势）")
    add("")
    if report.linear:
        _timeline(report.linear.timeline)
    add("")
    add("### 5.2 随机推演（混沌变量）")
    add("")
    if report.stochastic:
        add(f"<sub>视角：{report.stochastic.persona}｜temperature={report.stochastic.temperature}｜seed={report.stochastic.seed}</sub>")
        add("")
        _timeline(report.stochastic.timeline)
        if report.stochastic.branches:
            add("")
            add("**黑天鹅分支**")
            add("")
            for b in report.stochastic.branches:
                add(f"- {b}")
    add("")

    # 六、关键不确定性
    add("## 六、关键不确定性与监测信号")
    add("")
    if report.uncertainties:
        add("| 不确定性 | 影响 | 可能 | 监测信号 |")
        add("| --- | --- | --- | --- |")
        for u in report.uncertainties:
            add(f"| {u.topic} | {u.impact} | {u.likelihood} | {_join(u.monitoring_signals, '；')} |")
        add("")
        for u in report.uncertainties:
            add(f"- **{u.topic}**：{u.divergence}")
            add(f"  - 可能走向：{_join(u.outcomes, '、')}")
        add("")

    # 七、情景
    add("## 七、未来情景与概率")
    add("")
    add("| 情景 | 概率 | 生效时间 | 破坏程度 | 红利空间 | 来源 |")
    add("| --- | --- | --- | --- | --- | --- |")
    for s in report.scenarios:
        add(f"| {s.name} | {s.probability:.2f} | {s.effective_time} | {s.disruption} | {s.dividend_space} | {s.derived_from} |")
    add("")
    for s in report.scenarios:
        add(f"- **{s.name}**：{s.summary}（影响人群：{'、'.join(s.affected_groups) or '—'}；影响行业：{'、'.join(s.affected_industries) or '—'}）")
    add("")

    # 八、问题
    add("## 八、时代性问题清单（含根因与分析模型）")
    add("")
    for p in report.problems:
        add(f"### {p.id} {p.title}")
        add("")
        add(f"- 类别：{p.category}｜严重程度：{_stars(p.severity)}")
        add(f"- 分析模型：{_join(p.derived_models, '、')}")
        add(f"- 矛盾：{p.conflict}")
        add(f"- 根因：{p.root_cause or '—'}")
        add(f"- 为何未解决：{p.why_unsolved or '—'}")
        add(f"- 受影响人群：{_join(p.affected, '、')}")
        add(f"- 说明：{p.description}")
        if p.evidence_refs:
            add(f"- 证据出处：{'；'.join(p.evidence_refs)}")
        add("")

    # 九、评估 + 解法
    add("## 九、五维量化评估与结构化解法（按综合分排序）")
    add("")
    add("| 问题 | 难度 | 成本 | 紧急度 | 收益空间 | 综合分 |")
    add("| --- | --- | --- | --- | --- | --- |")
    problem_title = {p.id: p.title for p in report.problems}
    for e in report.evaluations:
        add(
            f"| {e.problem_id} {problem_title.get(e.problem_id, '')} | {_stars(e.difficulty)} | {e.cost_level} | "
            f"{_stars(e.urgency)} | {_stars(e.revenue_potential)} | **{e.score}** |"
        )
    add("")
    for e in report.evaluations:
        add(f"<details><summary>{e.problem_id} 解决路径与结构化解法</summary>")
        add("")
        add(f"- 成本估算：{e.cost_estimate or '—'}")
        add(f"- 标准化解决路径：{e.solution_path or '—'}")
        if e.method:
            m = e.method
            add(f"- 解法概述：{m.summary or '—'}")
            add(f"- 执行步骤：{_join(m.steps, ' → ')}")
            add(f"- 所需工具：{_join(m.tools, '、')}")
            add(f"- 所需知识：{_join(m.knowledge, '、')}")
            add(f"- 里程碑：{_join(m.milestones, '；')}")
            add(f"- 衡量指标：{_join(m.metrics, '；')}")
            add(f"- 最小可交付（MVP）：{m.mvp or '—'}")
            add(f"- 验证实验：{m.validation_experiment or '—'}")
            add(f"- 避坑点：{_join(m.pitfalls, '；')}")
        add("")
        add("</details>")
        add("")

    # 十、规划
    add("## 十、变现工程规划")
    add("")
    if report.plan:
        p = report.plan
        add("### 能力适配")
        add("")
        for k, v in p.capability_fit.items():
            if isinstance(v, list):
                add(f"- **{k}**：{'、'.join(str(x) for x in v)}")
            else:
                add(f"- **{k}**：{v}")
        add("")
        if p.roadmap_30_60_90:
            add("### 90 天落地路线图")
            add("")
            for phase in p.roadmap_30_60_90:
                add(f"#### {phase.window}｜{phase.goal}")
                add("")
                for task in phase.tasks:
                    add(f"- [ ] {task}")
                if phase.metrics:
                    add(f"- 验收指标：{_join(phase.metrics, '；')}")
                add("")
        add("### 短期落地任务")
        add("")
        for x in p.short_term_tasks:
            add(f"- [ ] {x}")
        add("")
        add("### 中长期趋势卡位")
        add("")
        for x in p.mid_long_positioning:
            add(f"- {x}")
        add("")
        add("### 变现路径")
        add("")
        for m in p.monetization_paths:
            add(f"- **{m.model}**｜定价：{m.pricing}")
            add(f"  - 前 100 个客户：{m.first_100_customers}")
            add(f"  - 里程碑：{m.milestone}｜关联问题：{'、'.join(m.related_problem_ids) or '—'}")
        add("")
        add("### 持续迭代学习")
        add("")
        for x in p.learning_loop:
            add(f"- {x}")
    add("")

    # 十一、风险
    add("## 十一、风险规避")
    add("")
    if report.plan:
        for x in report.plan.risks:
            add(f"- {x}")
    add("")

    # 附：信息源清单
    evidence = _evidence_index(report)
    if evidence:
        add("## 附一、信息源清单")
        add("")
        add("| 编号 | 信息断言 | 类型 | 来源 | 可信度 | 时效 |")
        add("| --- | --- | --- | --- | --- | --- |")
        for e in evidence:
            add(f"| {e.code or '—'} | {e.claim} | {e.source_type or '先验'} | "
                f"{e.source_hint or '模型先验'} | {e.credibility} | {e.recency or '—'} |")
        add("")

    if meta.warnings:
        add("## 附二、运行提示")
        add("")
        for w in meta.warnings:
            add(f"- {w}")
        add("")
    return "\n".join(lines)
