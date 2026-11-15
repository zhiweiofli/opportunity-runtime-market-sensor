# Changelog

## GitHub opportunity workflow — in progress

- 添加机会闭环和实践协议设计入口，以及业务 PR 路径边界的独立检查工具。该工具尚未接入 Actions，不能代替内容、合并证据或身份校验；机会闭环尚未启用。
- 记录 GitHub 接入检查和待接通的 Judge 提示词草稿。

## Deployment — 2026-10-20

- 导入 Opportunity Runtime 的指南、六份业务原稿、协议和 Market 0.2.0 代码/任务。
- 将原 Market workflow 模板部署到生效路径，增加 push/PR 离线 CI；输出规则、阈值及版本不变。
- 无正式行情规则、默认行情 schedule、自动交易、Drive 后端或其他业务角色。

本仓库后续业务行为变化须先改 spec，再改 task/code、版本及本文件；原始业务文档保持原文，实施协调写 docs/。

## Judge mirror/dashboard — 2026-11-14

Changed
- Judge 从每周一次调整为 Asia/Taipei 19:00 每 3 天一次，仍用 7 天证据窗口、每自然周 1 个新项目额度。
- 保持 Drive 主归档，新增 Google Docs 正文到私有 GitHub `or-archive/` 镜像及 manifest 对账。
- 新增静态 Pages 脱敏 Judge 决策看板；Pages 的真实发布状态需独立核实。

Reason
- 提高决策可见性和及时性，不增加 Judge 主动项目并行度。
