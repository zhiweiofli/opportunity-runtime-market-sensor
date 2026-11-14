<!-- Google Doc: https://docs.google.com/document/d/1Lk0Y_5oFT5BouOkjtaJ1wc7JOcUYv60HlEPPvAitFW4/edit?usp=drivesdk
Drive ID: 1Lk0Y_5oFT5BouOkjtaJ1wc7JOcUYv60HlEPPvAitFW4
Modified: 2026-10-28T09:56:42.878Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: Business-20261025-aws-shield-waf-antiddos-migration-toll


* Source Signal References:


   * Signal ID: Business-20261025-aws-shield-waf-antiddos-migration-toll
   * Generated At: 2026-10-28T09:15:01+08:00
   * Task Version: business-sensor@0.2.1
   * Source File URL: https://docs.google.com/document/d/1gkrUA9j_BltPCLMiXndpMykjH74Ru3bbcvDNdMxyx9M/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-28T09:15:01+08:00


* Research Level: R2 — Economic Underwriting


* Stage Result: HYPOTHESIS_READY


* Unknown Ledger:


   * Known: 2026年10月25日 AWS 正式执行 Phase 3 自动升级，终止为期 3 个月的免费评估期；AWS Shield Advanced 的 L7 自动防御强制替换为 AWS WAF 托管规则集（AWSManagedRulesAntiDDoSRuleSet），占用 50 WCU 容量；旧版 Shield L7 防御定于 2027年1月29日 彻底 Sunset；若用户在 10月25日 后仍将该规则集保持在 Count 模式，遭受 DDoS 攻击时将丧失请求费豁免（只有 Block 或 Challenge 模式才能减免突发流量费）；非 Shield 客户现在可按 $5/月 + $1/百万次请求独立开启该规则集，彻底打破以往每年 $36,000 的刚性合同门槛。
   * Unknown: 存量 Shield Advanced 企业客户中，有多少比例会在续约周期时选择主动降级/取消 $3,000/月的 Shield 合同，转而完全依靠 WAF 规则集防护。
   * Decision-Critical Unknown: 独立 DevOps/SecOps 工程师与中小 SaaS 团队对于一款“监控 AWS WAF DDoSAttackRequests 指标、在攻击发生瞬间自动在 1 秒内将规则由 Count 切换为 Challenge/Block 以规避天价账单，并自动化同步 Terraform/CDK 漂移的轻量无服务器守护中间件（定价 $29–$79/月）”的直接采购意愿。


* Gate Checks:


   * Money: 通过。中小团队从过去无法承受 $36,000/年的企业合同，到如今仅需 $5/月 WAF 规则费，抗 DDoS 门槛降低超 99%；同时自动升级若停留在 Count 模式会因失去豁免引爆数千美元突发账单，具备强烈的避险与省钱价值。
   * Mechanism: 通过。AWS 官方定价策略与计费豁免规则具有强约束力；无服务器探针（Lambda + CloudWatch 报警）毫秒级切换模式的技术机制清晰可行，彻底解决“怕误杀不敢开 Block，开 Count 又被账单背刺”的矛盾。
   * Persistence: 通过。AWS 官方 Phase 3 自动升级已于 2026年10月25日 强制执行，2027年1月29日 彻底下线旧版 Shield L7，云架构解耦不可逆。
   * Capture: 通过。1-3 人小团队构建轻量无服务器架构或 Terraform Module / CLI 工具，纯软件/代码交付，零实体资产、零硬件、高毛利。


* Final Status: HYPOTHESIS_READY


* Evidence:


   1. AWS Security Blog 官方架构与计费通告《AWS Shield Advanced is embracing the AWS WAF Anti-DDoS managed rule group》（2026-07-27，重大修订与执行日 2026-10-25）：证实 10月25日 自动升级、Count 模式丧失计费豁免、非 Shield 客户可独立 $5/月 启用。
   2. AWS 定价手册《AWS WAF Pricing》与《AWS Shield Advanced Pricing》：证实 $3,000/月 与 $5/月 之间的巨大门槛落差。
   3. AWS 官方代码迁移指南《AWS Shield Advanced L7 AMR Migration Helpers》：证实云端自动升级对 Terraform / CloudFormation 代码带来的漂移（Drift）与回退风险。


* Counter Evidence:


   1. 拥有大型专业 SecOps 团队的财富 500 强企业会自研跨账号 IaC 流水线同步，不需要外部第三方轻量工具。
   2. 部分对高可用极度敏感的金融级架构不愿采用自动化规则切换，宁愿承担潜在超额账单。


* Stop Reason: 四 Gate 均已通过充分独立证据核实，政策确定、门槛平民化与账单暴击痛点明确，小团队轻资产切入点极佳。


* Resume Condition: 不适用（已完成）。


* What became more likely: 中小云上团队将普遍独立启用 AWS WAF Anti-DDoS 规则集，并配套动态灵敏度与防暴击账单自动化策略。


* What became less likely: 中小团队继续为了基础 L7 DDoS 自动阻断而被迫采购每年 $36,000 的 Shield Advanced 合同。


* What did we rule out: 排除了在 10月25日 之后将 WAF Anti-DDoS 规则集长期保持在 Count 模式下仍能享受免费豁免的可能。


* Task Version: researcher@0.2.2


* Generated At: 2026-10-28T17:51:43+08:00


* Role Spec Status: reviewed


________________


Opportunity Hypothesis: AWS WAF Anti-DDoS 动态灵敏度与防暴击账单守护中间件（WAF Anti-DDoS FinOps Guard）
* Source Signal IDs: Business-20261025-aws-shield-waf-antiddos-migration-toll


* Source Signal References:


   * Signal ID: Business-20261025-aws-shield-waf-antiddos-migration-toll
   * Generated At: 2026-10-28T09:15:01+08:00
   * Task Version: business-sensor@0.2.1
   * Source File URL: https://docs.google.com/document/d/1gkrUA9j_BltPCLMiXndpMykjH74Ru3bbcvDNdMxyx9M/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-28T09:15:01+08:00


* Money: 全球数百万在 AWS 上运行 Web 业务的中小企业与高成长 SaaS 团队。过去无法承受每年 $36,000 的 Shield Advanced，如今仅需 $5/月 即可开启顶级 L7 抗 DDoS 规则，但面临“平时担心误杀设为 Count、遭遇攻击时丧失官方计费豁免引爆数千美元 WAF 账单”的结构性风险；团队愿按月支付 $29–$79 购买自动化守护探针。


* Mechanism: 工具基于 AWS 无服务器架构（EventBridge + Lambda + CloudWatch）：平时规则集处于 Count 或 Low 灵敏度确保业务零误杀；当 CloudWatch 检测到 DDoSAttackRequests 或请求突增达到攻击阈值时，探针在 1 秒内自动调用 WAFv2 API 将规则平滑提升为 Silent Browser Challenge 或 Block 模式，从而精准阻断恶意攻击并同时触发 AWS 官方“阻断模式下全额免收请求费”的计费豁免机制；攻击结束后自动回调灵敏度，兼顾业务可用性与财务防暴击。同时附带 IaC Drift 检测模块，自动同步 Terraform/CDK 状态，防止部署流水线覆写规则。


* Capture: 1-3 人小团队开发轻量级 Serverless 部署包或托管 SaaS 控制台，通过 AWS IAM Role 授权管理，纯 API 与代码驱动，零硬件、零库存、高毛利。


* Durability: AWS Phase 3 自动升级已于 2026-10-25 生效，2027-01-29 旧版下线，WAF 规则集与计费豁免规则长期确定，抗 DDoS 属于企业长期刚需。


* Evidence:


   1. AWS Security Blog（2026-10-25 升级）：https://aws.amazon.com/blogs/security/aws-shield-advanced-is-embracing-the-aws-waf-anti-ddos-managed-rule-group-what-changes-and-how-to-prepare/ 确认 Count 模式无豁免及独立解绑政策。
   2. AWS 定价手册：https://aws.amazon.com/waf/pricing/ 与 https://aws.amazon.com/shield/pricing/ 确认基准定价结构。
   3. AWS 官方代码助手：https://github.com/aws-samples/aws-shield-advanced-l7-amr-migration-helpers 确认 IaC 漂移风险。


* Counter Evidence:


   1. 超大型跨国客户拥有自建 SecOps 监控与 IaC 编排平台。
   2. 极少数企业完全使用 Cloudflare / Fastly 等外部 CDN，无需在 AWS 原生层防御。


* Critical Unknown: 中小企业 AWS 账号管理员对于授予外部 IAM Role 执行 WAF Rule Action 切换权限的安全合规接受度（可通过开源本地 CloudFormation 模板部署解决）。


* Falsification: 若 AWS 宣布在 Count 模式下同样对所有被标记为 DDoS 的攻击流量给予 100% 账单全免。


* Next Test: 开发单账号开源 Serverless 模板（Lambda + CloudWatch），在模拟 HTTP Flood 攻击环境下验证从 Count 到 Challenge 的触发延迟及 AWS 账单计量变化，邀请 3 家中型出海团队部署测试。


* Task Version: researcher@0.2.2


* Generated At: 2026-10-28T17:51:43+08:00


* Role Spec Status: reviewed