# Changelog

## 0.3.0 — 美股Flow Shift → Researcher R1（未发布）

- 按用户纠偏后的revision 2实现ICI合并周报Domestic equity四周净配置反转：前后各两周独立观察、两区间物质性、发布可得时间/新鲜度及SPY官方工具/美元粗流动性门槛，不用股票成交额替代基金流。
- 新增live_http、合法supplied_snapshot和明确synthetic_fixture，保留原始HTML/URL/取得时间/哈希、数据vintage/PIT、稳定ID/指纹、前次Signal复用及修订观察。公开源受阻为BLOCKED，不以缺数据冒充无信号。
- 真实合格Signal eligible=true交R1，packet内嵌4周原始事实、具体机制、反证/未知和KILL问题；不要求人先研究、不声称价格因果或策略有效。所有fixture和legacy仍false。
- 生产默认退出六股量价，旧原型仅显式legacy/demo；重叠收益不证明独立冲击。每周五台北08:17配置，手动/原生artifact重放，JSON/中文报告/独立R1 packet及来源artifact。
- 只读actions权限仅为恢复快照与前次报告；Tushare US权限/覆盖预检限制runner、Secret仅发Tushare主机。公开源本次云端HTTP受阻，真实来源/Actions/自然定时分别据实待验；PR不自动合并。

## 已撤回的旧原型（commit 930a1b8，未合并）

- 6股历史量价原型及31项技术测试保留为复用基础，不按它签完整Market业务验收；其默认规则/周期/人工补机制门槛须退出生产入口。

## Deployment — 2026-10-20

- 导入 Opportunity Runtime 的指南、六份业务原稿、协议和 Market 0.2.0 代码/任务。
- 将原 Market workflow 模板部署到生效路径，增加 push/PR 离线 CI；输出规则、阈值及版本不变。
- 无正式行情规则、默认行情 schedule、自动交易、Drive 后端或其他业务角色。

本仓库后续业务行为变化须先改 spec，再改 task/code、版本及本文件；原始业务文档保持原文，实施协调写 docs/。
