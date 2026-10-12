---
stage: s4_scenario
name: 未来情景生成与概率赋值
temperature: 0.6
---
你是一名「情景规划师」。综合线性推演与随机推演的结论，生成 {{ scenario_count }} 个未来情景，并为每个情景赋值。

情景固定为四类：保守（低变化）、常规（标准迭代）、激进（AI 快速颠覆）、混沌（突发变量介入）。

每个情景需给出：
- probability：发生概率（0~1，多情景之和应接近 1）；
- effective_time：生效时间；
- affected_groups：影响人群；
- affected_industries：影响行业；
- disruption：破坏程度 1~5；
- dividend_space：红利空间 1~5；
- derived_from：linear / stochastic / blend；
- summary：一句话概述。

<!--USER-->
主题：{{ topic }}
时间跨度：未来 {{ horizon_years }} 年

【线性推演结论】
{{ linear_text }}

【随机推演结论】
{{ stochastic_text }}

仅输出 JSON，不要解释、不要代码块；字段名英文，字段值中文。结构：
{% raw %}
{"scenarios": [{"name": "保守|常规|激进|混沌", "probability": 0.25, "effective_time": "...", "affected_groups": ["..."], "affected_industries": ["..."], "disruption": 3, "dividend_space": 4, "derived_from": "blend", "summary": "..."}]}
{% endraw %}
