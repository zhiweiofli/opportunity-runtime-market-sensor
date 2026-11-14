<!-- Google Doc: https://docs.google.com/document/d/1ALdHlHJSzCMFa1SUJhE5CS4OmASO8BOmlciTb3BsDLc/edit?usp=drivesdk
Drive ID: 1ALdHlHJSzCMFa1SUJhE5CS4OmASO8BOmlciTb3BsDLc
Modified: 2026-10-29T09:32:39.499Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: Business-20261028-github-enterprise-copilot-dollar-entitlement


* Source Signal References:


   * Signal ID: Business-20261028-github-enterprise-copilot-dollar-entitlement
   * Generated At: 2026-10-29T09:04:30+08:00
   * Task Version: business-sensor@0.2.1
   * Source File URL: https://docs.google.com/document/d/1KyXrLYilW-Jk1RyVSH1PEnGHC6YvoMLGTFW38GB_mOM/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-29T09:07:21+08:00


* Research Level: R2 — Economic Underwriting


* Stage Result: HYPOTHESIS_READY


* Unknown Ledger:


   * Known: 2026年10月28日 GitHub Universe 官方宣布重大商业与计费重构：1）GitHub Enterprise 全面打包内置 Copilot 访问权限，但彻底转向纯按量消耗计费（零预置点数，每个席位 0 免费月度 AI 积分，除基础代码补全外，Copilot Chat、PR 审查及云端智能体均从第 1 次请求起直接按量扣减企业实际预算）；2）彻底废除 Actions 固定运行时长分钟数（Runner Minutes），转为全平台统一的“以美元计价的共享算力权益额度”（Dollar-based shared compute entitlement），覆盖标准 Runner、大型托管构建机以及 2026年11月 正式计费的 Copilot 云沙盒（Cloud Sandboxes）；高单价的云沙盒长时间挂起将极速抽干整个组织的共享算力额度，使高频 AI 智能体任务与核心 CI/CD 自动部署流水线争夺同一笔美元预算。
   * Unknown: 中大型企业在 2026年11月 云沙盒正式扣费后，内部发生 CI/CD 流水线因额度耗尽而阻塞构建的实际频率与团队投诉率。
   * Decision-Critical Unknown: 拥有 50–500 名研发人员的 GitHub Enterprise 企业客户工程总监与 DevOps 负责人，对于一款“提供团队/仓库级 Actions 美元预算软硬配额切分、自动检测并回收挂起空闲超 15 分钟的 Copilot 云沙盒实例与僵尸快照的 FinOps 治理中间件（定价 $49–$199/月）”的直接采购意愿。


* Gate Checks:


   * Money: 通过。涉及全球数以万计 GitHub Enterprise 企业的年度 IT DevOps 与研发云算力预算；统一美元池使得原本确定性的固定 Actions 额度面临被 AI 云沙盒迅速抽干并引发突发大额超量账单的风险，企业具备刚性的控费与防熔断诉求。
   * Mechanism: 通过。商业收费站与算力统一度量衡重塑：Actions 分钟数向美元池迁移，高单价智能体算力与低单价流水线混池计费，制造了结构性的算力挤占摩擦；通过 GitHub Webhook 与 API 进行细粒度配额切分与闲置沙盒自动销毁在技术上完全可行且轻量。
   * Persistence: 通过。GitHub Universe 官方确立的核心平台计费架构重塑，已写入官方条款与产品路线图，2026年11月全面扣费，不可逆。
   * Capture: 通过。1-3 人小团队构建轻量 GitHub App / 管理中间件，纯 API 与 Webhook 驱动，零实体资产、零库存、高毛利 SaaS。


* Final Status: HYPOTHESIS_READY


* Evidence:


   1. GitHub Changelog 官方发布《GitHub Enterprise now includes access to GitHub Copilot》（2026-10-28）：证实全员内置 Copilot 但不包含月度 AI 积分，高阶 AI 任务从第 1 次请求起按量扣减企业预算。
   2. GitHub Changelog 官方发布《Work from anywhere with a new, connected Copilot cloud experience》（2026-10-28）：证实 Actions 分钟数变更为统一美元共享额度，覆盖标准构建机与 2026年11月 起正式计费的 Copilot 云沙盒。
   3. Adlega 2026 软件定价范式调研《SaaS Pricing Study 2026》（2026-10-23）：证实头部平台将固定席位费转变为按量消耗抽税的行业趋势。


* Counter Evidence:


   1. 拥有成熟平台工程团队的超大型科技巨头（千人以上）可能会通过自建 Internal Developer Portal (IDP) 内部脚本自行限制配额。
   2. GitHub 官方在未来版本可能在企业管理控制台中补齐粗粒度的组织用量限额。


* Stop Reason: 四 Gate 均已通过充分独立证据核实，政策与计费变革明确，研发预算争夺与沙盒防暴击痛点真实刚性，小团队切入点极佳。


* Resume Condition: 不适用（已完成）。


* What became more likely: 企业 DevOps 团队将必须为 GitHub Actions 引入细粒度的美元预算配额控制与云沙盒生命周期管理。


* What became less likely: 企业能继续放任开发人员随意开启多 surface 云端智能体会话而不建立用量监控。


* What did we rule out: 排除了在 GitHub 统一度量衡下云沙盒使用不会影响核心 CI/CD 流水线可用额度的假设。


* Task Version: researcher@0.2.2


* Generated At: 2026-10-29T17:29:33+08:00


* Role Spec Status: reviewed


________________


Opportunity Hypothesis: GitHub Actions 美元共享算力配额治理与 Copilot 云沙盒防蚕食控制器（GitHub Entitlement FinOps Guard）
* Source Signal IDs: Business-20261028-github-enterprise-copilot-dollar-entitlement


* Source Signal References:


   * Signal ID: Business-20261028-github-enterprise-copilot-dollar-entitlement
   * Generated At: 2026-10-29T09:04:30+08:00
   * Task Version: business-sensor@0.2.1
   * Source File URL: https://docs.google.com/document/d/1KyXrLYilW-Jk1RyVSH1PEnGHC6YvoMLGTFW38GB_mOM/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-29T09:07:21+08:00


* Money: 全球数万家使用 GitHub Enterprise 的中大型企业研发与 DevOps 预算；企业愿按月支付 $49–$199 购买自动化算力治理工具，以规避每月数千美元的突发超量账单及 CI/CD 停摆损失。


* Mechanism: 针对 GitHub 将固定 Actions 分钟数改为统一美元算力池、且 Copilot 云沙盒（Cloud Sandboxes）高费率持续消耗该额度的痛点，工具作为 GitHub App 挂载于企业组织：自动在部门/仓库级别切分美元额度；实时监控 AI 智能体沙盒与标准 CI/CD 构建的消耗比率；当某项目实验性沙盒快速烧钱时自动触发熔断预警或降级；并自动探测挂起超过 15 分钟的空闲沙盒快照触发休眠，锁定核心自动部署流水线的基本额度底线。


* Capture: 1-3 人小团队开发轻量级 GitHub App / 托管 SaaS，纯 API 与 Webhook，零硬件资产、零库存、高毛利。


* Durability: GitHub 官方已将统一美元权益与按量计费确立为核心平台战略，云端智能体与沙盒常态化，需求长期持续。


* Evidence:


   1. GitHub Changelog（2026-10-28）：https://github.blog/changelog/2026-10-28-github-enterprise-now-includes-access-to-github-copilot/ 确认按量扣减企业预算。
   2. GitHub Changelog（2026-10-28）：https://github.blog/changelog/2026-10-28-work-from-anywhere-with-a-new-connected-copilot-cloud-experience/ 确认 Actions 算力额度美元化及 11月 云沙盒扣费。
   3. Adlega SaaS Pricing Study（2026-10-23）：https://adlega.com/blog/saas-pricing-study-2026/ 确认按量算力抽税商业趋势。


* Counter Evidence:


   1. 拥有自建庞大内部基础设施的巨头会通过私有 Runner 规避。
   2. 极小型团队仅有单流水线，预算争夺不显著。


* Critical Unknown: 企业 IT 采购管理者对于授予第三方 GitHub App 组织级 Actions 与 Copilot API 读写/管理权限的合规审查周期。


* Falsification: 若 GitHub 官方在 11 月上线完全独立的、隔离的 Copilot 沙盒专用预算池，不允许其与 Actions CI/CD 共享额度互蚀。


* Next Test: 为 2 家拥有 30–80 名研发人员的 GitHub Enterprise 团队部署原型 Webhook 探针，监测 7 天内 Actions 构建与智能体调用的美元消耗分布，测试预算超限告警功能。


* Task Version: researcher@0.2.2


* Generated At: 2026-10-29T17:29:33+08:00


* Role Spec Status: reviewed