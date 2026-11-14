<!-- Google Doc: https://drive.google.com/file/d/11F420ngseJd4Gjf2n773utoQPv5x2Of-/view?usp=drivesdk
Drive ID: 11F420ngseJd4Gjf2n773utoQPv5x2Of-
Modified: 2026-10-20T09:52:31.337Z
Mirrored At: 2026-11-14 +08:00
-->

# Opportunity Runtime Research Record

- **Source Signal IDs**: Business-20261014-autodesk-aps-passthrough-billing
- **Source Signal References**:
  - Signal ID: Business-20261014-autodesk-aps-passthrough-billing
  - Generated At: 2026-10-20T08:15:00+08:00
  - Task Version: business-sensor@0.2.1
  - Source File URL: https://docs.google.com/document/d/1ZZbbgf9t75I6QhL5W-1xEMuT6_1w4Ft45GhuBuq-V48/edit?usp=drivesdk&ouid=101589702958564347595
  - Source File Modified At: 2026-10-20T08:13:59+08:00
- **Research Level**: R2 — Economic Underwriting
- **Stage Result**: HYPOTHESIS_READY
- **Unknown Ledger**:
  - Known: Autodesk 官方于 2026-10-14 全面开放 3LO 穿透计费；终端客户预付 Flex 额度（约 $3/Token）直接承接 Model Derivative 与 Design Automation 的 API 算力成本；纯 2LO / Server-to-Server 模式不支持穿透；存量 Client ID 切换为单向不可逆（Forward-only）。
  - Unknown: 中小型设计院在未采购企业级 Flex 额度时，对单次按需购买 Flex 以运行第三方插件的转化门槛；不同规模工程团队在 3LO 授权弹窗时的 IT 审批流程长度。
  - Decision-Critical Unknown: 建筑工程企业 BIM 主管对于外部第三方应用在 3LO 鉴权时消耗内部企业级 Flex 额度的审批授权与风控接受度。
- **Gate Checks**:
  - Money: 通过。资金池为建筑工程客户已采购常备的 Autodesk Flex Tokens 及 Enterprise Agreement (EA) 信用预算，API 成本直接向客户扣减，ISV 无需垫资。
  - Mechanism: 通过。打破此前 ISV 需为客户巨型 CAD/BIM 模型转换垫资导致的负边际毛利陷阱（“用得越多亏得越多”），使 ISV 软件成本结构回归轻量 SaaS，同时降低企业采购第三方软件的独立算力报销阻力。
  - Persistence: 通过。Autodesk 将 3LO 穿透计费列为核心长期基础设施演进，属于单向不可逆的架构变更，非短期营销或临时政策。
  - Capture: 通过。适合 1-3 人小团队构建轻量 Web/SPA 工具（如垂直 BIM 合规清洗、工程量自动提取、CAD 自动化报表），通过 3LO 用户鉴权直连官方 API，零服务器重资产、零垫资风险、高毛利。
- **Final Status**: HYPOTHESIS_READY
- **Evidence**:
  1. Autodesk 官方 ISV 指南《Passthrough billing: A guide for ISVs》（2026-10-05 发布，2026-10-14 生效）：https://aps.autodesk.com/blog/passthrough-billing-guide-isvs 明确 API 消耗直接由客户 Autodesk 账户承付，要求采用 3LO 并在授权中带入 `prompt=select_usage_context`。
  2. Autodesk 官方公告《Introducing passthrough billing: a more flexible way to manage API usage costs with APS》（2026-10-05）：https://aps.autodesk.com/blog/introducing-passthrough-billing-more-flexible-way-manage-api-usage-costs-aps 详述前后资金流与商业架构对比。
  3. Autodesk 官方产品视频《NEW CAPABILITY! Passthrough billing for Autodesk》（2026-10-05）：https://www.youtube.com/watch?v=zJG7OZqNpCQ 介绍第三方应用如何利用客户现有 Flex 额度消除 ISV 计费阻力。
- **Counter Evidence**:
  1. 客户准入门槛反弹：客户必须拥有包含 APS 配额的合格订阅或 Flex 额度；完全无 Flex 的小型设计事务所无法直接使用穿透应用。
  2. 纯后台批处理受阻：不支持纯 2LO（Server-to-Server）后台无感知批处理，必须有人工 3LO 上下文选择交互。
- **Stop Reason**: 四 Gate（Money, Mechanism, Persistence, Capture）已得到充分验证与深入核实，商业机制与技术约束清晰，已达到形成完整假设并进入实验验证的门槛。
- **Resume Condition**: 不适用（已完成）。
- **What became more likely**: 专注在特定 AEC 垂直场景（如合规报表、模型格式抽取）的轻量 SPA/Web 工具能够以近乎纯软件毛利快速切入大型企业客户。
- **What became less likely**: 纯后台无感知的离线定时脚本能够免密使用穿透计费（Autodesk 强制要求 3LO 交互上下文）。
- **What did we rule out**: 排除了在无客户授权上下文下由 ISV 继续垫资承担巨型 BIM 解析算力成本的必要性。
- **Task Version**: researcher@0.2.2
- **Generated At**: 2026-10-20T17:48:14+08:00
- **Role Spec Status**: reviewed

---

## Opportunity Hypothesis: 基于 Autodesk 3LO 穿透计费的垂直 BIM 轻量报表与合规校验 SPA

- **Source Signal IDs**: Business-20261014-autodesk-aps-passthrough-billing
- **Source Signal References**:
  - Signal ID: Business-20261014-autodesk-aps-passthrough-billing
  - Generated At: 2026-10-20T08:15:00+08:00
  - Task Version: business-sensor@0.2.1
  - Source File URL: https://docs.google.com/document/d/1ZZbbgf9t75I6QhL5W-1xEMuT6_1w4Ft45GhuBuq-V48/edit?usp=drivesdk&ouid=101589702958564347595
  - Source File Modified At: 2026-10-20T08:13:59+08:00
- **Money**: 建筑与工程（AEC）企业预付的 Autodesk Flex 额度（承担底层 Model Derivative 算力开销）+ 企业每年数百至数千美元的轻量合规工具 SaaS 订阅费。
- **Mechanism**: 穿透计费将高昂的模型解析算力完全剥离出开发者成本表，开发者毛利从过去潜在的负毛利飙升至 90% 以上；企业无需单独申请 API 外部采购预算，直接划扣内部现有 Flex 余额，成交流程大幅缩短。
- **Capture**: 1-3 人小团队开发轻量级 Web/SPA 应用，集成 Autodesk 官方 3LO（带 `prompt=select_usage_context`），专注于“施工图合规自动化检查”或“工程量清单瞬时抽取”，零重资产基础设施。
- **Durability**: Autodesk 官方确立长期 3LO 穿透演进，单向不可逆，平台战略支持 ISV 生态转移算力负担。
- **Evidence**:
  1. Autodesk 官方指南《Passthrough billing: A guide for ISVs》（2026-10-05）：https://aps.autodesk.com/blog/passthrough-billing-guide-isvs 明确 2026-10-14 起开放 3LO 穿透计费。
  2. Autodesk 官方公告《Introducing passthrough billing》（2026-10-05）：https://aps.autodesk.com/blog/introducing-passthrough-billing-more-flexible-way-manage-api-usage-costs-aps 证实客户直接承付 API 消耗。
  3. Autodesk 官方产品视频《NEW CAPABILITY! Passthrough billing for Autodesk》（2026-10-05）：https://www.youtube.com/watch?v=zJG7OZqNpCQ 说明 Flex 积分直接结算机制。
- **Counter Evidence**:
  1. 客户缺乏 Flex 额度导致无法开箱即用：若客户账户无可用 Flex，API 报错且流程中断。
  2. 纯后台批处理受限：不支持纯 2LO（Server-to-Server），限制了全自动离线流水线的集成深度。
- **Critical Unknown**: 建筑工程企业 BIM 主管对于第三方应用在 3LO 登录时消耗内部企业级 Flex 额度的审批授权与风控接受度。
- **Falsification**: 若多数企业 IT 在后台策略中集中封锁第三方应用消耗 Flex 额度，或要求极其繁重的跨部门财务审批。
- **Next Test**: 构建一个极简的开源/免费 BIM 报表 SPA 并在 Autodesk App Store 上架，验证 3LO `prompt=select_usage_context` 流程下中型 AEC 团队授权并消耗自身 Flex 额度的完成率。
- **Task Version**: researcher@0.2.2
- **Generated At**: 2026-10-20T17:48:14+08:00
- **Role Spec Status**: reviewed
