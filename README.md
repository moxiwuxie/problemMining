# AI时代趋势问题挖掘与变现规划系统

以「时代趋势迭代差」为数据源，用 LLM 模拟旧体系崩塌 → 新体系建立的过程，自动暴露未解决问题/缺口/痛点，五维量化后生成个人变现落地规划。

> 核心价值观：所有时代更替的痛点，都是普通人的变现机会。

## 安装

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev]"
```

## 快速开始（离线，无需 API Key）

```bash
./.venv/bin/python -m trendminer --topic "AI编程" --industry "软件" --dry-run
```

产物位于 `output/<run_id>/`：`report.md`、`report.html`，以及 8 个阶段的 `stage_*.json`。

## 真实调用

```bash
cp .env.example .env      # 填入 LLM_API_KEY
./.venv/bin/python -m trendminer --topic "AI医疗" --industry "医疗" --provider deepseek
```

provider（deepseek / qwen / openai，均为 OpenAI 兼容协议）在 [config/providers.yaml](config/providers.yaml) 配置，运行参数与评分权重在 [config/settings.yaml](config/settings.yaml)。

## CLI 参数

| 参数 | 说明 |
| --- | --- |
| `--topic` | 主题（必填） |
| `--industry` | 行业/领域 |
| `--horizon` | 时间跨度（年），默认 5 |
| `--persona` | 目标人群，默认「普通职场人」 |
| `--scenarios` | 情景数量，默认 4 |
| `--focus` | 关注重点，可重复传入 |
| `--provider` | 覆盖 provider |
| `--formats` | 输出格式，默认 `md,html` |
| `--seed` | 随机推演种子 |
| `--dry-run` | 使用 Mock LLM 离线回放 fixtures |
| `--resume` | 复用同 run_id 已有阶段产物 |
| `--out` | 输出根目录 |

## 管线（8 阶段）

1. s1 趋势信息检索（旧存量 + 新增量 + 空白点）
2. s2 关键节点拆解（时代拐点）
3. s3a 线性推演 + s3b 随机推演（并发）
4. s4 未来情景生成 + 概率归一化
5. s5 自动暴露时代性问题
6. s6 五维量化评估（难度/成本/紧急度/收益/解决路径）+ 综合评分
7. s7 变现工程规划
8. s8 报告渲染（Markdown + HTML）

## 测试

```bash
./.venv/bin/python -m pytest
```

## 目录

```
config/      运行配置与 provider 定义
prompts/     每阶段一个 prompt（YAML front-matter + 正文）
src/trendminer/
  llm/       LLM 客户端、JSON 解析、Mock 回放
  pipeline/  8 个阶段 + 编排器
  render/    Markdown / HTML 渲染
templates/   HTML 模板
tests/       单元 + 离线端到端测试 + fixtures
output/      生成的报告与阶段产物
```
