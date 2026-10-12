# AI时代趋势问题挖掘与变现规划系统 — 实施方案

## Context（为什么做 / 目标）

当前目录 `problemMining` 为空仓库（greenfield）。用户在需求中给出了一套完整设计：以「时代趋势迭代差」为数据源，用 LLM 模拟时代演进的「旧体系崩塌 → 新体系建立」过程，自动**暴露未解决问题/缺口/痛点**，并**五维量化 + 生成个人变现落地规划**，形成「发现问题 → 评估问题 → 解决问题 → 获取报酬 → 持续迭代」的闭环。

目标产出：一个可运行的 Python 系统（CLI），输入一个主题/行业，输出可读的**问题挖掘与变现规划报告**（Markdown + HTML），全过程分阶段可落盘、可调试、可离线测试。

## 关键决策（请在批准时确认或调整）

本环境无 `AskUserQuestion` 工具，故先取以下默认值，均可通过配置文件覆盖：

1. **LLM 提供方**：默认 **OpenAI 兼容协议**（`base_url` 可切 DeepSeek / Qwen / OpenAI），密钥走环境变量。默认 provider = `deepseek`。
2. **检索层实现**：MVP 由 LLM 先验 + 可选真实搜索接口双轨。先定义 `SearchProvider` 抽象接口，默认 `NullSearchProvider`（纯 LLM）；预留 `TavilySearchProvider` 后续接入。**注意：不接真实搜索时，检索层结论本质是模型先验，会标注 `source_hint` 与 `confidence` 提示可信度。**
3. **交付形态**：本地 Markdown + HTML 报告；飞书推送（复用 lark 能力）留作可选增强，不阻塞 MVP。

## 项目结构

```
problemMining/
├── pyproject.toml                 # 依赖: requests, pyyaml, jinja2, pydantic, pytest
├── README.md                      # 使用说明（唯一新增文档）
├── .env.example                   # LLM_API_KEY 等占位
├── config/
│   ├── settings.yaml              # 默认 provider、max_retries、output_dir、max_tokens、evidence 上限
│   └── providers.yaml             # deepseek/qwen/openai: base_url / model / api_key_env / temperature
├── prompts/                       # 每阶段一个 prompt（YAML front-matter + 正文 + JSON schema 约束）
│   ├── 01_retrieval.md
│   ├── 02_inflection.md
│   ├── 03a_linear.md
│   ├── 03b_stochastic.md
│   ├── 04_scenarios.md
│   ├── 05_problems.md
│   ├── 06_evaluation.md
│   └── 07_plan.md
├── src/trendminer/
│   ├── __init__.py  __main__.py
│   ├── cli.py                     # argparse 入口
│   ├── config.py                  # 加载 YAML + env，产出 Settings/ProviderConfig
│   ├── models.py                  # 全部 pydantic 数据模型
│   ├── prompts.py                 # 加载 md + jinja2 渲染
│   ├── context.py                 # PipelineContext：结果容器 + 分阶段落盘 + resume
│   ├── llm/
│   │   ├── client.py              # LLMClient：requests 调 /chat/completions，重试/退避
│   │   ├── parser.py              # 脏 JSON 提取/修复（剥 ```json、括号匹配、未闭合补全）
│   │   └── mock.py                # MockLLMClient：离线回放 fixtures
│   ├── search/
│   │   ├── base.py                # SearchProvider 抽象
│   │   └── null.py                # NullSearchProvider（默认）
│   ├── pipeline/
│   │   ├── orchestrator.py        # 顺序编排 8 阶段
│   │   ├── s1_retrieval.py        # 检索（旧存量 + 新增量）
│   │   ├── s2_inflection.py       # 关键节点识别
│   │   ├── s3a_linear.py          # 线性推演
│   │   ├── s3b_stochastic.py      # 随机推演
│   │   ├── s4_scenario.py         # 4情景 + 概率归一
│   │   ├── s5_problems.py         # 自动暴露问题
│   │   ├── s6_evaluation.py       # 五维量化
│   │   ├── s7_plan.py             # 变现工程规划
│   │   └── s8_report.py           # 汇总 + 渲染
│   └── render/
│       ├── markdown.py            # PipelineReport -> report.md
│       └── html.py                # jinja2 -> report.html
├── templates/report.html.j2
├── tests/
│   ├── fixtures/llm/*.json        # 各阶段离线回放数据
│   ├── conftest.py                # mock_client / tmp_output_dir / sample_topic fixtures
│   ├── test_parser.py
│   ├── test_llm_client.py
│   ├── test_models.py
│   ├── test_mock_pipeline.py      # 全 8 阶段端到端（离线）
│   └── test_render.py
└── output/<run_id>/               # 交付物：report.md / report.html + stage_NN_*.json
```

## 数据模型（`models.py`，pydantic BaseModel）

- `TopicInput`: topic, industry, horizon_years, persona, scenario_count, focus[], locale
- `Evidence{claim, category(规则/岗位/商业模式/技术/政策/空白), source_hint, confidence}`；`RetrievalResult{old_era[], new_era[], gaps[]}`
- `InflectionNode{node_type(技术落地/行业重构/政策变更/用户习惯/商业模式失效新生), description, trigger_signals[], eta, impact_score}`
- `Hypothesis{horizon(短/中/长), statement, drivers[], blockers[], confidence}`；`ReasoningOutput{mode, timeline[], branches[], persona, temperature, seed}`
- `Scenario{name(保守/常规/激进/混沌), probability, effective_time, affected_groups[], affected_industries[], disruption, dividend_space, derived_from}`
- `Problem{id, title, category(能力错配/工具流程错配/行业空白/个体生存焦虑/企业降本淘汰/AI配套缺失), description, evidence_refs[], conflict}`
- `Evaluation{problem_id, difficulty(1-5), cost_level + cost_estimate, urgency(1-5), revenue_potential(1-5), solution_path, score(加权)}`
- `Monetization{model(服务/课程/工具/SaaS/咨询), pricing, first_100_customers, milestone}`；`Plan{capability_fit, short_term_tasks[], mid_long_positioning[], monetization_paths[], learning_loop[], risks[]}`
- `PipelineReport{topic_input, retrieved, inflections, linear, stochastic, scenarios, problems, evaluations, plan, run_meta}`

**一致性约束**：`scenarios` 概率归一化到和为 1；`Problem.id` → `Evaluation.problem_id` → `Plan` 引用一致；`score` 由五维加权（权重在 settings.yaml）。

## 编排与持久化

`orchestrator.run(input, cfg) -> PipelineReport`，严格顺序；
- s3a 与 s3b 无依赖，**并发执行**（`concurrent.futures.ThreadPoolExecutor`，requests 为 IO 密集）。
- 每阶段落盘 `output/<run_id>/stage_NN_<name>.json`（含原始 LLM 响应 + 解析后模型），`run_meta.json` 记录输入哈希、provider/model、timings、dry_run。
- `--resume <run_id>`：已有有效阶段 JSON 则跳过。
- 错误策略：LLM 调用失败 → 指数退避重试（429/5xx）；JSON 解析失败 → 一次「修复重试」；仍失败 → s3b 等可选阶段降级跳过并标记，核心阶段中断但保留已落盘结果。

## LLM 客户端

`LLMClient.chat(messages, *, response_format_json=True, temperature, seed) -> str`
- `requests` 直连 OpenAI 兼容 `/chat/completions`；provider 由 `providers.yaml` 决定 base_url/model/api_key_env，`--provider` 覆盖。
- JSON 输出：优先 `response_format={"type":"json_object"}`；不支持则 prompt 强约束 + `parser.extract_json` 兜底。
- 重试：429/5xx 指数退避（1s/2s/4s，max_retries=3），4xx 抛 `LLMError`。

## Prompt 策略

每阶段一个 md：角色 + 任务 + **必须输出的 JSON schema** + 正/反例，结尾统一「仅输出 JSON，字段名英文，值中文」。
- **线性推演**：temperature≈0.2，要求 短→中→长 连续时间线，只允许已知确定性变化。
- **随机推演**：temperature≈0.9 + 注入随机 `persona`（末日论者/技术乐观派/资本视角/监管视角）+ `seed`，**强制输出 `branches` 且至少 2 条与主线无关的黑天鹅**，保证与线性结果真正发散。

## Mock / dry-run（保证离线可测）

`--dry-run` 时用 `MockLLMClient` 按 `stage` 名读 `tests/fixtures/llm/{stage}.json` 回放，零网络请求；`MOCK_SEED` 可轻微扰动以验证并发分支。使 pytest 全链路无 API key 可跑。

## 测试策略（pytest）

- 单元：[test_parser.py](file:///Users/xiaoxu/Desktop/PycharmProjects/problemMining/tests/test_parser.py) 覆盖脏/截断/```json；`test_llm_client.py` 覆盖重试与 4xx；`test_models.py` 覆盖校验与概率归一。
- 集成：`test_mock_pipeline.py` 跑全 8 阶段，断言字段齐全、概率和为 1、problem→evaluation→plan 引用一致。
- 渲染：`test_render.py` 断言 md/html 含关键章节与中文标题。

## CLI

```
python -m trendminer --topic "AI编程" --industry "软件" --horizon 5 --scenarios 4 \
  --out output/ --provider deepseek --dry-run --resume <run_id> --formats md,html
```

## 分阶段构建顺序

1. 脚手架：pyproject / config / models / parser，`test_parser` 通过。
2. LLMClient + mock + fixtures（离线可跑）。
3. **竖直切片**：s1 + s2 + 落盘 + 最小 md 渲染 → 首个可运行产物。
4. 补齐 s3a / s3b / s4 / s5（核心价值链）。
5. s6 / s7 + 完整 md/html 报告。
6. 重试 / resume / CLI 完善 + 全链路 pytest。

## 验证方式

1. `pip install -e ".[dev]"`（或 `pip install -r requirements.txt`）。
2. `pytest -q` → 全部离线测试通过（Mock 模式，无需密钥）。
3. `python -m trendminer --topic "AI编程" --dry-run --out output/` → 生成 `output/<run_id>/report.md` 与 `report.html`，检查 8 个阶段 JSON 齐全。
4. 配好 `LLM_API_KEY` 后去掉 `--dry-run` 真实跑一次，人工检查报告质量与 JSON 解析成功率。

## 风险

- LLM 长 JSON 截断 → 限制每阶段 evidence 条数 + `parser` 修复 + `max_tokens` 配置。
- 情景概率不自洽 → 强制归一化。
- 无真实搜索时检索层为模型先验 → 标注 confidence，后续接入 `SearchProvider`。
- token 成本 → 限制上下文条目数。
