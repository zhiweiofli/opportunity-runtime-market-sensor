<!-- Google Doc: https://drive.google.com/file/d/1HwxZTGX8G3HyzXBHKfev4UD017pCJFHA/view?usp=drivesdk
Drive ID: 1HwxZTGX8G3HyzXBHKfev4UD017pCJFHA
Modified: 2026-10-22T09:46:05.981Z
Mirrored At: 2026-11-14 +08:00
-->

# Opportunity Runtime Research Record

- **Source Signal IDs**: Friction-20261022-ShopifySubscriptionPaymentMigration
- **Source Signal References**:
  - Signal ID: Friction-20261022-ShopifySubscriptionPaymentMigration
  - Generated At: 2026-10-22T09:37:00+08:00
  - Task Version: friction-sensor@0.2.1
  - Source File URL: https://drive.google.com/file/d/17NFaE9ddhiqlFrOprky_f7ixuw1_IItV/view?usp=drivesdk
  - Source File Modified At: 2026-10-22T09:38:14+08:00
- **Research Level**: R1 — Quick Structure
- **Stage Result**: KILL
- **Unknown Ledger**:
  - Known: Shopify 订阅商户在跨应用（如从 Recharge 迁移至 Shopify Subscriptions 或 Skio/Loop）或切换支付网关时，面临存量支付令牌（Payment Token / Vault ID）未验证、PayPal 授权失效等断点；但经深入调研，底层信用卡敏感数据跨库迁移严格受 PCI-DSS Level 1 合规管辖（必须由原始网关与目标网关通过加密 PGP/SFTP 点对点传输，第三方无权介入拦截）；同时，主流订阅应用厂商（如 Skio, Loop, Stay AI 以及 Recharge 自身）为了争夺高净值商户，普遍将“免费白手套迁移服务（Free White-Glove Migration）”作为获客获单的标配赠送。
  - Unknown: 迁移过程中因终端消费者忽略更新邮件导致最终不可逆流失的行业中位数比例。
  - Decision-Critical Unknown: 无（已在 R1 确认强反证并终止）。
- **Gate Checks**:
  - Money: 未通过。商户在迁移时普遍依赖目标订阅平台提供的免费迁移配套服务，缺乏向独立第三方软件单独支付高额项目费的持续预算。
  - Mechanism: 未通过。底层卡号令牌传输受 PCI-DSS 严格合规约束，必须在合规金库（Vaults）之间直接流转，中间层第三方工具无法直接处理敏感明文；而分批测试与客户通知属于一次性项目制实施服务，不存在持续滚动的软件机制。
  - Persistence: 未通过。对单个商户而言，系统与网关迁移是数年一遇的低频一次性事件（One-off project），完全缺乏按月/按年持续订阅付费的生命周期价值（LTV），无法支撑可持续的独立产品业务。
  - Capture: 未通过。面对目标 SaaS 厂商将迁移支持作为获客成本（CAC）免费补贴赠送的残酷竞争，且伴随极其繁重的人工跨网关协调与客服答疑（重人力、高客服），完全违背 1-3 人小团队“轻资产、低客服、高毛利”偏好。
- **Final Status**: KILL
- **Evidence**:
  1. StackScale 行业迁移实操指南《[Shopify Subscription Payment Migration Guide (2026)](https://stackscalehq.com/shopify-subscription-payment-migration/)》（2026-10-15 发布）：明确指出“Import success is not payment readiness”，详述商户必须针对不同支付渠道（Stripe、PayPal、Shopify Payments）分批逐步测试验证。
  2. Shopify 官方帮助中心规范《[Migrating payment methods to your Shopify account](https://help.shopify.com/en/manual/products/purchase-options/subscriptions/migrating-payment-methods)》（2026-10）：官方明确要求支付令牌的跨账户迁移必须遵循严格的合规流程，且部分渠道需商户直接联系支付处理商处理。
  3. Succession Media 订阅竞品横向迁移追踪《[Recharge Alternatives: What Breaks When You Switch Apps](https://succession.media/guides/switch-subscription-apps-recharge/)》（2026-10-04）：揭示新一代订阅软件厂商（如 Skio、Stay AI、Loop）均提供端到端免费白手套代迁移服务，商户无需自行采购第三方中介软件。
- **Counter Evidence**:
  1. 一次性低频事件而非持续循环痛点：单店迁移完成即终结，缺乏长期软件复购与留存。
  2. 目标平台免费内卷：竞品为了撬单普遍包揽迁移工程，第三方独立工具缺乏定价权。
  3. PCI 合规与高客服约束：涉及信用卡金库跨机构迁移，合规门槛极高且长尾客诉极重。
- **Stop Reason**: 存在足够强反证可 KILL。该摩擦属于典型的低频一次性项目事件（非持续摩擦），商业模式被目标 SaaS 平台的免费白手套撬单服务内卷吸收，且受制于 PCI-DSS 支付安全壁垒与极重人工客服，无法形成小团队轻资产独立软件机会。
- **Resume Condition**: 不适用（已 KILL）。
- **What became more likely**: Shopify 订阅商户在迁移时将继续依赖新选型平台的专业支持团队进行协同交付。
- **What became less likely**: 市场上能跑通一款纯按软件订阅收费的通用“Shopify 订阅支付迁移”独立工具。
- **What did we rule out**: 彻底排除了将一次性网关数据迁移工程当作结构性持续软件产品机会的可能。
- **Task Version**: researcher@0.2.2
- **Generated At**: 2026-10-22T17:42:35+08:00
- **Role Spec Status**: reviewed
