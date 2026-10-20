# Changelog

## Unreleased — Market 0.3.0 开发需求

- 用户授权补齐历史量价异常、固定观察名单、质量/流动性过滤、台北工作日调度及人工候选核验需求，见 docs/market-v1-requirements.md。
- 此条只记录已入Git的开发规格；实现、实际任务版本和部署仍待开发PR，不代表正式策略有效或定时已实跑。

## Deployment — 2026-10-20

- 导入 Opportunity Runtime 的指南、六份业务原稿、协议和 Market 0.2.0 代码/任务。
- 将原 Market workflow 模板部署到生效路径，增加 push/PR 离线 CI；输出规则、阈值及版本不变。
- 无正式行情规则、默认行情 schedule、自动交易、Drive 后端或其他业务角色。

本仓库后续业务行为变化须先改 spec，再改 task/code、版本及本文件；原始业务文档保持原文，实施协调写 docs/。
