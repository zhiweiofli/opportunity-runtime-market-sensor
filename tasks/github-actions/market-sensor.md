---
task_id: market-sensor
version: 0.2.0
platform: github-actions
role_spec: docs/03-market-sensor.md
role_spec_status: reviewed
guide_basis: PROJECT_GUIDE.md §3.3, §6, §14, §19
updated_at: 2026-10-19
---

# Market Sensor（已核对原稿，演示骨架）

负责 fetch → calculate → filter → detect anomaly。确定性工作只用 Python；不交给 LLM 凭感觉扫描市场。
依据 `docs/03-market-sensor.md`、`docs/00-overview.md` 及指南完成角色边界核对。`reviewed` 仅代表对照过原稿，不代表正式异常规则、账户/API 或平台已验收。

## 搭配与验收

[仓库设置手册](../../README.md) 给出本地运行、Secret、Actions 表单及报告保存步骤；[验证记录](../../docs/validation.md) 区分本地、Actions 与真实 API 证据。此角色只运行确定性代码。正式规则待用户提供，接线通过不代表真实机会。

## 当前边界

- 只演示 `abs(pct_chg) >= 显式阈值`。`pct_chg` 直接使用 Tushare 基于除权昨收计算的百分数，不用未复权价格自行推导收益率。
- 阈值参数名为 `--demo-abs-pct`，所有结果有 `demo_only: true`、`rule.status: demo_only`、`research_eligible: false`。原稿未指定正式市场、标的、指标、比较基准、阈值、频率，不能把本骨架称作正式异常策略。
- 只实现 daily 的单日单标的接入；flow/spread/carry/volatility/relative value/valuation/regime change 等在指南关注范围内，但本阶段没有实现。
- `fixture` 是合成数据（不是行情），固定日期 2026-10-16；应产生两个演示 Signal。真实 Tushare 数据也仅检验接线，不能当真实机会输入 Researcher。
- `persistence: 一次性` 只描述本次单日观察，实际持续性未知；不能凭单日跳动推断持续/正在扩大。未识别具体钱流与机制，明确未知。

## 原稿规则与输出核对

正式类型为 Flow Shift / Relative Mispricing / Carry / Basis / Volatility Mispricing / Positioning Extreme / Regime Shift。本演示不强行归类为其中任何一种。

正式输入优先结构化行情、量、期货/期权、ETF Flow、利率、FX、商品、基本面、宏观、仓位数据；文本仅解释异常，不生成核心 Signal。本阶段只覆盖单日行情入口，未实现其余观察指标。

报告中每条演示 Signal 保留原稿的 `anomaly / instrument / magnitude / persistence / possible_mechanism / data_quality / next_question`，并保留指南统一字段和任务版本。`data_quality` 披露合成/实连未验、单点、无历史基准及流动性未验证；百分比变化不是历史分位或错价结论。

正式交 Research 必须同时具备：可量化异常、足够历史背景、非单个价格跳动、潜在经济机制、可交易工具、流动性不明显不足。本骨架不满足，报告显式禁止升级。快速 Kill 条件：数据不足、异常不可重复、流动性不足、成本吃掉收益、无 convergence/catalyst、仅“价格便宜”、纯宏观叙事、依赖拿不到的数据。

交易研究须回答 What is mispriced / Why / Why does it persist / What closes the gap / How long / What does it cost to express / What invalidates it，然后进入 Backtest / Walk-forward / Out-of-sample / Slippage / Transaction Cost / Capacity / Risk 数据验证；本阶段仅声明交接边界，不实现这些验证或交易。

## 运行与输出

见根目录 README 的离线及 Tushare 命令。Python 3.9+，标准库实现，无第三方依赖。

输出 JSON 包括 `task_id / task_version / role_spec_status / generated_at / source / demo_only / research_eligible / research_blockers / trade_date / ts_code / rule / status / observations / signals`。

| status | 含义 |
| --- | --- |
| `SIGNALS` | 数据有效且匹配演示规则；不是机会结论 |
| `NO_MATCH` | 有数据但未匹配演示规则 |
| `NO_DATA` | 数据源返回空，不能断言休市或无异常 |
| `ERROR` | 参数、凭据、网络/API 或数据校验失败，退出码非零 |

完成命令行解析后的每次运行写入完整快照，运行错误时也覆盖旧快照并输出空 Signal，防止把上次成功当本次成功。未知选项/缺少选项值等命令行语法错误在运行前退出，不生成新报告；须核对退出码和报告时间。报告写入失败仍非零退出，控制台报错，不宣称输出成功。非有限数值、缺失字段、日期/单标的不符都会失败，不将坏数据悄悄过滤为无异常。Token 仅从 `TUSHARE_TOKEN` 读取，不保存在报告，不回显服务端原始错误体。

Evidence 保留当前原始行情记录和接口字段定义；两条来自同一数据提供者，**不是两个独立市场证据**。合成样本引用本地 fixture，绝不伪造外部行情出处。

## Actions 人工配置

1. `.github/workflows/market-sensor.yml` 是本仓库生效配置，`tasks/github-actions/market-sensor.yml` 保留同步副本。
2. 配置提交到默认分支后，在 Actions → Market Sensor → Run workflow 手动运行。实际部署/验收状态见 `docs/validation.md`。
3. 默认 source=`fixture`、demo_abs_pct=`5`，无密钥。先检查离线测试、报告和 artifact。
4. 如需实连，在仓库 Actions Secret 中配置 `TUSHARE_TOKEN`，选择 `tushare`，填写 `trade_date`（YYYYMMDD）和 `ts_code`（单一标的）。接口权限、HTTPS 可达性及实际返回需另验。
5. 下载 `market-report-<run_id>-<attempt>` artifact；人工放 `Signals/Market/` 或附给 Researcher。演示结果仅验管线，不能用于真实判断。

没有默认 schedule；周期待正式规则及试跑确认后，在生效 workflow 里人工添加，遵循平台当前时区和默认分支规则。不建立额外 scheduler。

## 人工运行卡（可复制）

```text
Task: market-sensor@0.2.0
Role Spec Status: reviewed
Source: fixture / tushare
Trade Date: <Tushare 必填 YYYYMMDD；fixture 固定 20261016>
TS Code: <Tushare 必填，单一标的；fixture 留空>
Demo Abs Pct: <正数，单位百分数，如 5 代表 5%；只作管线演示>
Output: outputs/market/report.json 或显式不同文件名
核对：source、demo_only、status、日期、标的、原始 observations、signals、任务版本。
交接：演示产物不进入真实机会判断；保留未验证项并人工保存报告。
```

技术依据及未验证项见 `docs/validation.md`。不实现交易、回测策略、自动上传、自动提交数据或自动平台部署。
