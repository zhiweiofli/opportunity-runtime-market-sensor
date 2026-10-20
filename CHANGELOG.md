# Changelog

## 0.3.0 — 历史量价监测试运行（待合并部署）

- 用户授权补齐历史量价异常、固定观察名单、质量/流动性过滤、台北工作日调度及人工候选核验需求，见 docs/market-v1-requirements.md。
- 按版本化小名单查询550自然日 daily，使用此前252个5日复合收益基准、成交额倍数、同向持续、流动性与新鲜度过滤；严格拒绝未来/重复/坏数据，披露逐标的覆盖，错误抑制整轮候选。
- 增加中文 Markdown/JSON 双报告、实际配置与SHA-256、稳定ID/排序及截断计数；正常串行节流、有限网络重试，保留原单日demo入口和八项兼容测试。
- 真实历史标为 demo_only=false / rule.status=trial，所有统计候选仍 research_eligible=false。fixture 永远合成，机制与表达成本另作人工核验。
- Market workflow 增加历史重放和工作日台北20:17定时配置，仅runner使用既有Secret，仍只读仓库；自然定时须合并后独立验收，不代表交易策略有效。

## Deployment — 2026-10-20

- 导入 Opportunity Runtime 的指南、六份业务原稿、协议和 Market 0.2.0 代码/任务。
- 将原 Market workflow 模板部署到生效路径，增加 push/PR 离线 CI；输出规则、阈值及版本不变。
- 无正式行情规则、默认行情 schedule、自动交易、Drive 后端或其他业务角色。

本仓库后续业务行为变化须先改 spec，再改 task/code、版本及本文件；原始业务文档保持原文，实施协调写 docs/。
