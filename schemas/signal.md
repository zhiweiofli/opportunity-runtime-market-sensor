# Signal 协议 — 0.2.0

依据 `docs/00-overview.md`、三个 Sensor 原稿及 `PROJECT_GUIDE.md` §6 核对。公共字段用于跨平台追溯，角色字段保持原稿语义；口径协调见 `docs/README.md`。此处是文档协议，不建设 schema 服务。

```text
Signal ID: <类型-日期-稳定主题标识；重复观察可追溯>
Type: Business / Friction / Market
What Changed: <变化、时间和比较基准>
Money: <哪笔真实资金、收入、成本或资产；未知明确标注>
Evidence: <2–4 条最重要原始证据，来源定位、日期与事实；不把转引当独立证据>
Mechanism: <经济意义；区分事实、推断和未知>
Persistence: <按角色取值，见下表>
Next Question: <最可能改变判断的问题>
Task Version: <生成任务实际版本，如 business-sensor@0.2.1 或 market-sensor@0.2.0；不是协议版本>
Generated At: <ISO 8601，含时区>
Role Spec Status: reviewed
```

| Type | 必须保留的角色字段 | Persistence |
| --- | --- | --- |
| Business | Magnitude: Small / Medium / Large 及依据 | Temporary / Emerging / Persistent |
| Friction | Friction、Current Workaround（含成本）、Payer、Economic Effect | Temporary / Structural |
| Market | Anomaly、Instrument、Magnitude、Possible Mechanism、Data Quality | 一次性 / 持续 / 正在扩大 |

Friction 另尽量记录 Friction Value ≈ Frequency × Economic Loss per Event × Recoverable Rate，未知明确披露，不编造精确数字。Market 的 Anomaly / Possible Mechanism 与公共 What Changed / Mechanism 对应；Data Quality 要说明可靠性与历史长度，不能用单日涨跌冒充历史分位或经济错价。

Signal 不是 Opportunity，不得直接 Build。各 Sensor 先核对自身研究触发与快速 Kill 条件：Business 不达标线索为 IGNORE/WATCH，Friction 不达标保持 WATCH；它们不是 Hypothesis。没有证据时可返回 NO_SIGNAL，访问受阻为 BLOCKED，均为运行说明而非伪造 Signal。

Market JSON 的 `signals[]` 使用上述字段的 snake_case。`magnitude` 记录量化幅度及历史分位（无历史为 null）；`data_quality` 记录 synthetic / history_points / history_sufficient / liquidity_verified / reliability。`evidence` 是 source / observed_at / fact 对象数组。

运行级 `status / source / demo_only / rule / observations` 区分数据与规则来源、无数据和无匹配。当前所有 Market 产物都有 `demo_only: true`、`research_eligible: false` 及运行级 `research_blockers`，不得进入真实机会研究。仅行情记录和提供者接口说明不是两份独立市场证据，不能冒充满足正式研究条件。

`reviewed` 只指本地原稿核对，不意味着外部平台实测或 Market 正式规则验收。`0.1.0` 历史输出保留原版本，不能直接重标。
