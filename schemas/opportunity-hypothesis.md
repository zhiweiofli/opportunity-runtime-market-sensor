# Research / Opportunity Hypothesis 协议 — 0.2.1

依据 `docs/04-researcher.md`、`docs/00-overview.md`、Market 原稿 §8 及指南 §4/§7/§8。状态协调详见 `docs/README.md`。

Research 记录必须保留 Source Signal IDs、Research Level、Stage Result、Unknown Ledger（Known / Unknown / 一个 Decision-Critical Unknown）、已检查的 Gate 及证据、Final Status、停止原因、每轮三问、版本和时间。R1 未评估的 Gate 明示未评估，不强行做完整 R2。

`researcher@0.2.2` 另须输出 Source Signal References，逐条含 `Signal ID / Generated At（输入观察时间） / Task Version（来源 Sensor 版本） / Source File URL / Source File Modified At（可获得时）`。观察键为前三项，源文件修改时间用于发现同键原地更新；来源用本轮粘贴全文时注明标题/段落和人工输入。它补充 Source Signal IDs，不取代原字段。默认目录选取、已处理/等待恢复/旧记录覆盖不明、保存后才持久生效的规则见 [输入选取约定](../docs/research-intake.md)。

`0.2.0` 历史记录仍可交 Judge，不改标；缺观察引用时不能仅凭同 ID 自动判定覆盖当前版本，应核对对应输入。Final Status 和 Hypothesis 字段语义不变。

| 阶段 | 内容 / 默认证据预算 | Stage Result / 路线 |
| --- | --- | --- |
| R1 Quick Structure | Money / Mechanism；3–5 个高质量原始来源 | KILL / ESCALATE |
| R2 Economic Underwriting | 四 Gate 与反证；8–12 个真正独立来源 | KILL / WATCH / HYPOTHESIS_READY |
| R3 Decision Research | 仅 1 个关键未知，不追求来源数量 | Decision Route: VALIDATE / TRADE RESEARCH / PASS（建议） |

Final Status 只取 KILL / HYPOTHESIS_READY / BLOCKED；HYPOTHESIS_READY 对应原稿 HYPOTHESIS READY。WATCH 是 R2 阶段结果；本轮停止且需等待证据时 Final Status=BLOCKED，并写恢复条件。ESCALATE 与 Decision Route 不当最终结论或执行授权。

只有四个 Gate（Money / Mechanism / Persistence / Capture）均有足够依据且 Final Status=HYPOTHESIS_READY，才生成：

```text
Opportunity Hypothesis: <标题>
Source Signal IDs: <输入引用>
Money: <哪笔钱>
Mechanism: <价值从哪里产生>
Capture: <可占据的节点>
Durability: <为什么不会快速消失>
Evidence: <3–5 条最强证据，原始来源、日期、支持事实>
Counter Evidence: <原稿 Counter-Evidence，1–3 条最强反证；未找到明确披露，不凑数>
Critical Unknown: <最可能改变决策的 1 个未知>
Falsification: <什么观察会立即推翻>
Next Test: <最低成本验证，由人决定执行>
Task Version: <生成任务实际版本，如 researcher@0.2.2；不是本协议版本>
Generated At: <ISO 8601，含时区>
Role Spec Status: reviewed
```

每轮必须回答 What became more likely / What became less likely / What did we rule out。来源预算不授权无限搜索，也不允许凑来源；反证缺口应披露，并纳入成熟度判断。

任一停止条件成立即停止：足够强反证、四 Gate 足够回答、关键未知只可靠现实实验/结构化数据/私有信息解决、下一轮公开搜索不太可能改变 Decision。Cashflow 回答 payer/金额/频率/毛利归属/原因/成本可缩/小团队可经营即可停；Friction 回答受影响者/损失/workaround/成本/payer 后转现实验证建议。

Trading 另须回答 What is mispriced / Why / Why does it persist / What closes the gap / How long / What does it cost to express / What invalidates it，然后停止叙事研究，转交 Backtest / Walk-forward / Out-of-sample / Slippage / Transaction Cost / Capacity / Risk 验证。假设不是已验证策略，不执行交易。
