# Changelog

## GitHub opportunity workflow — in progress

- 看板标签中文语义化（仅显示层，数据与原文保留英文代码，悬停可见）：研究结论 HYPOTHESIS_READY/KILL/BLOCKED/WATCH → 假设就绪/已否决/待实证/观察中；评审判定 NOW/NEXT/WATCH/DROP → 本周推进/排队候选/观察/放弃；来源 Business/Friction/IBF/UW → 利润池变化/付费摩擦/存量困局/人工不划算；类型改为信号/研究/研究批次回执/评审/归档。新增 `site/labels.js` 统一映射；运行回执卡片摘要改为批次状态与产出数，不再误摘研究结论。
- 看板移除“PR / Issue 闭环状态”区块与旧版 `latest.json` 手工快照：删除 `site/workflow.js`、`site/data/latest.json`、`scripts/workflow/build_snapshot.py` 及其测试；Pages 工作流不再生成 `workflow.json`，去掉 PR/Issue 事件触发和相应只读权限（推送、定时、Drive 同步后的显式触发保留）。页头改为显示简报生成与最近 Judge 时间（UTC+8），历史资料区增加类型、原文状态、来源标签的筛选说明。闭环机制（任务交接、决策提案、协议校验）不受影响。
- 新增 `scripts/workflow/build_brief.py` 从只读 `drive-mirror/manifest.json` 生成 `site/data/brief.json`（`or-brief@1`）并接入 `judge-pages.yml`，首屏新增“本期简报”展示流水线健康状态、最新 Judge 结论/决策看板/待决定事项、上次 Judge 之后的新 Research 及非裁决性质的“可能重复历史 KILL”提示；零待办时自动收起 PR / Issue 闭环与旧版 `latest.json` 手工快照，历史资料列表默认隐藏 `no-signal` 记录。
- `brief.json` 增加 `trends`、`judge_history`、`source_yield`、`coverage_gaps` 与 `judge_coverage` 健康项（Judge 回看窗口 7 天）；“本期简报”重排为健康条、重点关注（NOW 突出，WATCH/DROP 仅计数）、原生 SVG 机会趋势，以及默认收起的 Judge 未覆盖 Research 与新 Research 列表。
- 增加默认关闭的 Drive 只读单向镜像与页面索引接入，按文件 ID 与已有镜像去重；身份、公开范围和在线运行仍需配置验证。
- 四项现有定时补扫改为每三小时一次，事件触发和手动触发继续保留。
- 历史卡片支持按原文最终状态和文件名明确标识的来源标签筛选；未知值不推断。
- 历史资料入口移至页面后部，以正文提取的标题和摘录提供卡片及搜索；保留原文链接和主动展开方式。
- 看板新增按需打开的历史资料浏览入口，可搜索 Research 与 Judge 镜像并跳转原文，不改变机会或任务统计。
- 为任务交接补充读取提交状态的权限，以排查合并后补扫遇到的 403；只授予状态读取权限，实际恢复仍需线上验证。
- 添加机会闭环和实践协议设计入口，以及业务 PR 路径边界检查。机会闭环尚未启用。
- 记录 GitHub 接入检查和待接通的 Judge 提示词草稿。
- 增加机会、任务、结果和决定的 v1 Schema，及引用、任务哈希、证据、时间、金额和 GitHub 合并事实检查。新增可信 base 校验工作流草案；首次引入本工作流的 PR 仍须人工审查。
- 增加任务 Issue 补扫、串行租约与人类决定提案的实现草案；账号变量、GitHub Actions 权限、通知及外部消费者均须实际接通和验收，不能将本地模拟算作上线。
- 保留原 Judge 快照并新增闭环看板和仅使用显式脱敏字段的静态投影；公开投影默认关闭，首次启用须确认字段披露范围。GitHub 请求失败时不部署新快照。
- 公开范围未确认时，所有 Pages 部署入口均保持关闭，包括主分支推送和手动触发；确认范围后才启用部署。
- 任务可经新评审 PR 重新批准；旧租约绑定旧 hash，时长预算跨运行累计。结果可附带逐项哈希验证的同运行证据文件。
- 结果的执行时段须有对应的中心领取与租约回执；main 中的机会、任务、结果和决定在消费前重新核验合并来源。合成机会和零费用测试消费者与真实业务分开标记、配置和统计。

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
