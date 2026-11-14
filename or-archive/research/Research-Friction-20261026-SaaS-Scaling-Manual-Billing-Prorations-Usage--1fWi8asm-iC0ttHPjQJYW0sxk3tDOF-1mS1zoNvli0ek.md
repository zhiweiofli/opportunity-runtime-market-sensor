<!-- Google Doc: https://docs.google.com/document/d/1fWi8asm-iC0ttHPjQJYW0sxk3tDOF-1mS1zoNvli0ek/edit?usp=drivesdk
Drive ID: 1fWi8asm-iC0ttHPjQJYW0sxk3tDOF-1mS1zoNvli0ek
Modified: 2026-10-26T09:58:47.263Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: Friction-2026-10-26-SaaS-Scaling-Manual-Billing-Prorations-Usage
* Source Signal References:
   * Signal ID: Friction-2026-10-26-SaaS-Scaling-Manual-Billing-Prorations-Usage
   * Generated At: 2026-10-26T09:37:00+08:00
   * Task Version: friction-sensor@0.2.1
   * Source File URL: https://drive.google.com/file/d/1Gq_xw3KvwhYYF4JmqVn9qbw_3xcTusBE/view?usp=drivesdk
   * Source File Modified At: 2026-10-26T09:39:06+08:00
* Research Level: R1 — Quick Structure
* Stage Result: KILL
* Unknown Ledger:
   * Known: 早期 SaaS 企业在从少量大客户发票制向成百上千自助订阅用户过渡时，若仍使用电子表格（Spreadsheets）手动计算比例分摊（Prorations）、用量账单（Usage Billing）和递延收入确认，确实会遭遇流程混乱与人工核算崩溃；但经深入调研，该问题属于早期初创公司在规模化过程中必经的经典阶段性运维阵痛，在市场上早已存在极其成熟、完备且高度标准化的商业解决方案（包括主流聚合网关自带的 Stripe Billing、Chargebee、Paddle、Recurly 以及开源/专业的用量计量计费引擎 Lago、Metronome、Orb 等）；Reddit 原帖当事人本质是在寻求从手工向现有成熟系统的迁移选型经验（“what did you end up using?”），社区同行一致建议直接启用 Stripe Billing 或 Chargebee，明确指出“无需重复造轮子（No point reinventing the wheel）”。
   * Unknown: 早期初创团队在坚持手工电子表格记账至多少 MRR 阶段会必然发生开票中断。
   * Decision-Critical Unknown: 无（已在 R1 确认强反证并终止）。
* Gate Checks:
   * Money: 未通过。处于该阶段的企业预算高度明确，其购买力直接流向成熟的头部计费基础设施（直接采购 Stripe Billing 或 Chargebee），不存在向第三方全新通用计费工具付费的增量软件预算。
   * Mechanism: 未通过。比例分摊（按日/按秒精确折算退款与抵扣）、周期中变配（Mid-cycle plan changes）和用量聚合（Usage metering）属于已被 Stripe Billing 和 Lago 原生完全解决的标配功能。不存在因底层技术断层或规则变更产生的新套利机制。
   * Persistence: 未评估（R1 阶段终止）。
   * Capture: 未通过。该赛道已被千亿级支付巨头（Stripe）与独角兽（Chargebee、Maxio）以及高星开源项目（Lago）彻底覆盖；小团队研发通用计费系统需要维护极其沉重的全球税务合规（Stripe Tax/Avalara）、发卡行风控、本地网关与高复杂度财务审计追溯，完全违背 1-3 人小团队“轻资产、低客服、高毛利”偏好。
* Final Status: KILL
* Evidence:
   1. Reddit r/SaaS 原帖讨论《How did you handle subscription billing as your SaaS scaled?》（2026-10-22 发布）：早期创始人求助如何处理规模化计费，社区主流回答为“90% 的 SaaS 产品订阅模型高度一致，直接使用成熟的 Stripe Billing / Chargebee，不要重复造轮子”。
   2. Reddit 同主题讨论《When did you move beyond Stripe for usage based SaaS billing?》（2026-10-21）：证实专业服务商（如 Stripe 官方合作伙伴）与开源工具均能标准接入，属于现有成熟生态的实施配置范畴。
   3. Lago 开源用量计费与计量引擎官方架构文档（2026-10）：详述开源体系已将复杂的按量计费、事件去重与比例计算完全代码化开源提供。
* Counter Evidence:
   1. 市场已有标准答案且巨头高度内卷：Stripe Billing、Chargebee、Paddle 已完全标准化解决该摩擦。
   2. 属于临时性成长过渡阶段而非永久市场真空：公司规模化后只需切换至成熟计费系统即可永久消除电子表格手工摩擦。
* Stop Reason: 存在足够强反证可 KILL。该摩擦属于早期创业企业从手工过渡到标准软件过程中的经典运维阶段，已有行业公认的标准商业答案与成熟巨头垄断，且涉及沉重财务审计与全球税务客服，不符合小团队轻资产进入约束。
* Resume Condition: 不适用（已 KILL）。
* What became more likely: 规模化中的 SaaS 企业将加速接入 Stripe Billing 或 Chargebee 以淘汰手工表格。
* What became less likely: 独立小团队能以纯软件模式重新发明一套通用 SaaS 订阅与用量计费引擎并获得商业成功。
* What did we rule out: 彻底排除了将早期团队因未采购现有成熟软件导致的手工表格摩擦误判为新软件产品机会的可能。
* Task Version: researcher@0.2.2
* Generated At: 2026-10-26T17:56:05+08:00
* Role Spec Status: reviewed