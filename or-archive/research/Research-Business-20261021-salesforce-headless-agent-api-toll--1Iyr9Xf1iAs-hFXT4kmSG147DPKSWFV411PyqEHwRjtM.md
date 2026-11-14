<!-- Google Doc: https://docs.google.com/document/d/1Iyr9Xf1iAs-hFXT4kmSG147DPKSWFV411PyqEHwRjtM/edit?usp=drivesdk
Drive ID: 1Iyr9Xf1iAs-hFXT4kmSG147DPKSWFV411PyqEHwRjtM
Modified: 2026-10-24T09:27:28.926Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: Business-20261021-salesforce-headless-agent-api-toll
* Source Signal References:
   * Signal ID: Business-20261021-salesforce-headless-agent-api-toll
   * Generated At: 2026-10-24T09:10:16+08:00
   * Task Version: business-sensor@0.2.1
   * Source File URL: https://docs.google.com/document/d/1eB5tsI2rZeNSsBEIPIgF31tjKXc829UlzgYQqsuZjiM/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-24T09:15:20+08:00
* Research Level: R2 — Economic Underwriting
* Stage Result: HYPOTHESIS_READY
* Unknown Ledger:
   * Known: Salesforce 官方知识库（Article 005360285）正式定义外部注册 AI 智能体（通过 MCP 或标准 REST/SOQL）对生产环境发起的每一次调用均为 Headless Platform Interaction (HPI)，并消耗企业 Flex Credits（基准牌价 $500 / 100,000 Credits，折合 $0.005/点，超额按月后付且未用完不滚存）；而沙盒环境（Sandbox）全额免费，传统非智能体系统间批量同步（Scheduled Sync）维持原有配额不收 HPI 费用；2026-10-21 Salesforce 高层介入生态磋商，正加紧推进定于 11 月正式执行的计费落地；由于单次任务中智能体通常发起 5-20 次多轮细碎往返，企业面临严重的“模型 Token + 平台接口过路费”双重账单（Double Billing）冲击。
   * Unknown: Salesforce 即将在 30 天通知期内正式公布的单次 HPI 最终扣点乘数（Multiplier，目前标为 TBA）。
   * Decision-Critical Unknown: 拥有活跃外部 AI 智能体（Claude / ChatGPT / 自研 Agent）的 Salesforce 中大型企业客户，对于能够通过本地/网关请求编译将 10 次多轮细碎 Agent 往返自动打包为单次 Salesforce Composite/GraphQL 批量调用以削减 70%90% HPI 过路费的压缩中间件（如 $99$299/月），其采购决策速度与 IT 审批壁垒。
* Gate Checks:
   * Money: 通过。全球超 15 万家企业客户在 Salesforce 上的直接 IT 预算池，Flex Credits 具备 $500/100k 的清晰标价，单次高频业务调用产生可量化的新增硬支出。
   * Mechanism: 通过。双重套利机制：1) New Toll Booth：Salesforce 对 Agentic Identity 设置独立的计费闸口；2) Batching Arbitrage：官方单次 HPI 按“往返请求次数”而非“返回数据量”计费，且传统批量同步免收 HPI 费。通过将智能体的多轮交互（查 Schema -> 搜线索 -> 查商机 -> 填备注）在网关侧编译为单次 Composite 批处理请求，直接抹除 80% 的过路费账单。
   * Persistence: 通过。Salesforce 已将 HPI 纳入 Digital Wallet 和官方 Customer 360 计费底层管线，并将其作为全生态变现核心战略，非短期营销测试。
   * Capture: 通过。1-3 人小团队可利用开源 MCP 协议或代理中间件，构建“Salesforce HPI 智能压缩网关（HPI Call Compactor）”与“沙盒流量基线审计探针”，纯 API/Webhook 软件形态，零重资产、零线下交付、高毛利。
* Final Status: HYPOTHESIS_READY
* Evidence:
   1. Salesforce 官方帮助文档（Article 005360285）《Understand AIforce Impact》（2026-09 发布，2026-11 执行）：官方明确定义 MCP 与直接 API 均按 HPI 计量扣减 Flex Credits，沙盒免费。
   2. Salesforce Ben 生态深度报道《Salesforce Opens Talks With Partners Over AI Agent Billing Concerns》（2026-10-21）：证实伙伴对双重计费的强烈担忧，指出架构师正普遍寻求多请求合并技术以规避按次扣费。
   3. Vantage Point 行业合规指南《Salesforce Will Meter Agentic MCP and API Calls》（2026-10-10）：确认 Flex Credits 牌价为 $500/100,000点，提示企业必须在上线前完成调用频次基线测算。
* Counter Evidence:
   1. 乘数 TBA 延迟：具体单次扣点倍数目前尚未官宣，若最终定额极低（如 1 点/次），企业痛感可能不及预期；但若按 Agentforce 交互等效折算，成本压力极大。
   2. 原生 Agentforce 竞争：Salesforce 极力推销自身全托管的 Agentforce，但企业普遍因定制能力更倾向于外部 Claude/OpenAI 智能体。
* Stop Reason: 四 Gate 均已通过充分独立证据核实，政策确定、痛点清晰、机制与套利空间坚实。
* Resume Condition: 不适用（已完成）。
* What became more likely: 企业架构师将强制要求外部智能体在访问 Salesforce 时通过批量 Composite 聚合网关以降低往返频次。
* What became less likely: 外部智能体可以继续免密/共用普通集成账号无限次免费调用生产环境 Salesforce 接口。
* What did we rule out: 排除了 Salesforce 会因伙伴反对而彻底废止 Agentic Identity 独立收费的可能（底层基础设施已就绪）。
* Task Version: researcher@0.2.2
* Generated At: 2026-10-24T17:22:32+08:00
* Role Spec Status: reviewed


________________


Opportunity Hypothesis: 面向外部 AI 智能体的 Salesforce HPI 请求压缩网关与沙盒基线探针
* Source Signal IDs: Business-20261021-salesforce-headless-agent-api-toll
* Source Signal References:
   * Signal ID: Business-20261021-salesforce-headless-agent-api-toll
   * Generated At: 2026-10-24T09:10:16+08:00
   * Task Version: business-sensor@0.2.1
   * Source File URL: https://docs.google.com/document/d/1eB5tsI2rZeNSsBEIPIgF31tjKXc829UlzgYQqsuZjiM/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-24T09:15:20+08:00
* Money: 企业在 Salesforce Digital Wallet 中购买并储备的 Flex Credits 预算（$500/100k）；企业愿支付节省接口过路费的 20%~30% 作为网关订阅费。
* Mechanism: 针对 Salesforce 将注册智能体单次 API/MCP 往返判定为 1 次 HPI 并扣减积分的规则，网关作为外部 Agent（Claude/Cursor）与 Salesforce 之间的透明代理，智能拦截多轮细碎查表动作，将其动态编译为单次 Salesforce Composite Batch 或 GraphQL 多字段查询；同时利用只读数据缓存，将每轮业务结果的 HPI 调用频次从 15 次降低至 1-2 次。
* Capture: 1-3 人小团队构建轻量级反向代理（支持 MCP 协议与 REST），并提供免费的“沙盒环境 HPI 流量审计探针”作为获客漏斗，纯软件 SaaS，零重资产。
* Durability: Salesforce 官方建立 Agentic 独立计费管道不可逆，大模型 Agent 普及加速调用量增长。
* Evidence:
   1. Salesforce 官方文档（2026-09）：https://help.salesforce.com/s/articleView?id=005360285&language=en_US&type=1 明确生产环境 HPI 按次扣减 Flex Credits。
   2. Salesforce Ben（2026-10-21）：https://www.salesforceben.com/salesforce-opens-talks-with-partners-over-ai-agent-billing-concerns/ 证实生态急需请求合并方案以规避高额扣费。
   3. Vantage Point 行业指南（2026-10-10）：https://vantagepoint.io/blog/sf/salesforce-flex-credits-agentic-api-calls 测算企业生产上线成本压力。
* Counter Evidence:
   1. 官方扣点乘数若极度廉价可能削弱节省动力。
   2. Salesforce 可能限制第三方 Composite 调用的嵌套层级。
* Critical Unknown: 企业 IT 安全团队对于在 Agent 与生产 Salesforce 之间串联第三方请求聚合代理的合规审计门槛。
* Falsification: 若 Salesforce 最终取消针对标准 API 的 HPI 计费，重新对外部 Agent 开放免费无限制配额。
* Next Test: 开发一个开源 MCP Proxy 原型，在本地演示将 5 步常见 CRM 交互（获取联系人、商机、历史备注）压缩为 1 次 Composite API 调用，发布到开发者社区测试性能与积分节省率。
* Task Version: researcher@0.2.2
* Generated At: 2026-10-24T17:22:32+08:00
* Role Spec Status: reviewed