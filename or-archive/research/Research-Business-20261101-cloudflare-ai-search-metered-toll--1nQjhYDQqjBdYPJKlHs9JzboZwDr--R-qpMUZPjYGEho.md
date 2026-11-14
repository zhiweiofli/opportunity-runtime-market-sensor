<!-- Google Doc: https://docs.google.com/document/d/1nQjhYDQqjBdYPJKlHs9JzboZwDr--R-qpMUZPjYGEho/edit?usp=drivesdk
Drive ID: 1nQjhYDQqjBdYPJKlHs9JzboZwDr--R-qpMUZPjYGEho
Modified: 2026-11-01T09:49:48.680Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: Business-20261101-cloudflare-ai-search-metered-toll


* Source Signal References:


   * Signal ID: Business-20261101-cloudflare-ai-search-metered-toll
   * Generated At: 2026-11-01T09:11:05+08:00
   * Task Version: business-sensor@0.2.1
   * Source File URL: https://docs.google.com/document/d/13yAys9Gb16f2MvsQgwDdUvLvRdoIsUFP09AzC2vUE8k/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-11-01T09:14:30+08:00


* Research Level: R2 — Economic Underwriting


* Stage Result: HYPOTHESIS_READY


* Unknown Ledger:


   * Known: 2026年11月1日，全球最大边缘网络服务商 Cloudflare 官方正式对旗下 AI Search（将 Workers AI、Vectorize、R2 存储及 Browser Run 爬虫整合为一体的无服务器搜索管道）开启正式按量计费（Usage-based billing）；除每月赠送额度外，严格执行分层计费：基础数据摄入 $0.75 / 100万 tokens，图片/PDF OCR 额外加收 $0.50 / 100万 tokens，索引内置存储高达 $2.00 / GB-月（是标准 R2 对象存储 $0.015/GB-月的 133 倍），语义/混合检索 $0.75 / 1,000 次，全文检索 $0.10 / 1,000 次；官方规定按分块分词（cl100k_base）后的所有重叠文本（Chunk Overlap）在每个分块中均被重复独立计费，导致企业在 RAG 构建中面临摄入膨胀、高昂存储税与高频语义检索账单暴击。
   * Unknown: 部署在 Cloudflare Workers 上的中型企业 RAG 应用中，长尾冷文档占知识库总存储的比例中位数。
   * Decision-Critical Unknown: 使用 Cloudflare Workers 架构部署企业知识库与 AI 智能体应用的工程主管，对于一款能够“在边缘端自动剔除重叠样板文本、将低频冷数据降级留存至廉价 R2、并将精准关键词查询智能分流至 $0.10 全文检索通道的 FinOps 优化网关（定价 $29–$89/月 或按节省账单抽成 15%）”的直接采购意愿。


* Gate Checks:


   * Money: 通过。涉及全球数十万使用 Cloudflare Workers 部署 RAG 与 AI 知识库的企业与开发者预算；存储税（$2.00/GB vs $0.015/GB）高达 133 倍，语义检索费（$0.75/1k）是全文检索的 7.5 倍，日均 50 万次检索的应用每月产生数百至数千美元按量账单，具备强烈的省钱动力。
   * Mechanism: 通过。商业收费站（New Toll Booth）与套利机制清晰：Cloudflare 将散装基础设施整合为边缘一键托管管道并加收高毛利过路费；轻量边缘中间件（运行于 Workers）在数据入库前剔除重叠冗余，并在查询时通过极小尺寸意图分类器分流语义与全文请求，技术闭环简单确定。
   * Persistence: 通过。Cloudflare 官方 GA 产品正式计费生效（2026-11-01），边缘知识库与自主智能体属于长期基础设施架构。
   * Capture: 通过。1-3 人小团队构建基于 TypeScript/Workers 的开源 SDK + 托管路由控制台，纯软件与 API 交付，零实体资产、零硬件、高毛利。


* Final Status: HYPOTHESIS_READY


* Evidence:


   1. Cloudflare 官方定价与配额文档《Limits & pricing - Cloudflare AI Search docs》（2026-10-30 更新，2026-11-01 生效）：证实摄入 $0.75/M、存储 $2.00/GB-月、语义查询 $0.75/1k 及重叠分块重复计费规则。
   2. Cloudflare 官方博客 GA 通告《AI Search is now generally available》（2026-10-01 发布，2026-10-30 计费确认）：证实底层整合 Workers AI, Vectorize 与 R2 的全托管无服务器管道。
   3. Cloudflare Changelog 发布说明《AI Search is generally available》（2026-10）：确认商业计费正式执行。


* Counter Evidence:


   1. 极小型个人玩具项目使用月度免费配额（5M tokens / 10GB）即可满足需求，无需付费优化。
   2. 具备丰富底层基础设施经验的大型团队会自行编写 Vectorize + Workers AI 拼装代码。


* Stop Reason: 四 Gate 均已通过充分独立证据核实，政策确定、平台计量卡点明确、架构套利空间清晰，小团队轻资产切入点极佳。


* Resume Condition: 不适用（已完成）。


* What became more likely: Cloudflare 生态内的 RAG 开发者将普遍在前端接入分块去重与多层级存储（Hot AI Search + Cold R2）优化中间件。


* What became less likely: 开发者继续将全量非结构化历史日志与文档未经压缩清洗直接推入 AI Search 托管存储。


* What did we rule out: 排除了在 11月1日 计费正式生效后开发者仍能无限量免费调用 Cloudflare 边缘嵌入与多模态检索的可能性。


* Task Version: researcher@0.2.2


* Generated At: 2026-11-01T17:47:41+08:00


* Role Spec Status: reviewed


________________


Opportunity Hypothesis: 面向 Cloudflare AI Search 的边缘 RAG 存储去重压缩与查询意图智能分流网关（Edge RAG Cost Optimizer）
* Source Signal IDs: Business-20261101-cloudflare-ai-search-metered-toll


* Source Signal References:


   * Signal ID: Business-20261101-cloudflare-ai-search-metered-toll
   * Generated At: 2026-11-01T09:11:05+08:00
   * Task Version: business-sensor@0.2.1
   * Source File URL: https://docs.google.com/document/d/13yAys9Gb16f2MvsQgwDdUvLvRdoIsUFP09AzC2vUE8k/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-11-01T09:14:30+08:00


* Money: 全球数以万计基于 Cloudflare Workers 构建知识库客服、AI 搜索与智能体记忆的企业团队；企业面对每月数十至数百美元的超额存储税与高频检索账单，愿按月支付 $29–$89 或按削减账单金额的 15% 购买优化中间件。


* Mechanism: 针对 Cloudflare AI Search 11月1日 开启计费后存储单价高达 $2.00/GB（是 R2 的 133 倍）且语义检索（$0.75/1k）是全文检索（$0.10/1k）7.5 倍的痛点，中间件提供双重优化：1）数据入库前执行分块智能去重与样板清除，将低频冷文档留存在标准 R2（$0.015/GB）仅提取关键词索引，只将高频热向量注入 AI Search 托管存储，削减 60%–80% 存储费；2）在边缘 Workers 运行极轻量规则与分类器，将包含型号、专有名词、ID 等精确匹配查询直接分流至 $0.10/1k 全文检索，仅对复杂长句放行至 $0.75/1k 语义检索，大幅降低查询端过路费。


* Capture: 1-3 人小团队构建开源 TypeScript 客户端 SDK + 边缘 Cloudflare Worker 代理模板，纯软件/API，零硬件、零库存、高毛利。


* Durability: Cloudflare 官方计费费率长期固定，边缘 RAG 架构属于生成式应用的核心基础设施，需求具备长期粘性。


* Evidence:


   1. Cloudflare 官方定价文档（2026-10-30）：https://developers.cloudflare.com/ai-search/platform/limits-pricing/ 证实 11月1日 计费执行、费率明细及重叠分块计费规则。
   2. Cloudflare 官方博客（2026-10-01）：https://blog.cloudflare.com/ai-search-ga/ 确认全托管 RAG 架构。
   3. Cloudflare Changelog（2026-10）：https://developers.cloudflare.com/changelog/post/2026-10-01-ai-search-generally-available/ 确认 GA 与计费转换。


* Counter Evidence:


   1. 纯免费额度范围内的极小型爱好者项目无需优化。
   2. 少数完全不用全文检索纯依赖向量相似度的极简用例。


* Critical Unknown: 典型出海中型企业知识库中，能够被规则分流至 $0.10 全文检索通道的实际查询请求占比。


* Falsification: 若 Cloudflare 官方主动下调 AI Search 存储单价至与 R2 相同水平（$0.015/GB-月），并对语义检索提供无限量免费额度。


* Next Test: 开发单文件 Cloudflare Worker 查询路由代理，在模拟 10 万次混合查询数据集（包含 50% 关键词匹配与 50% 语义推理）上测试路由命中准确率与官方账单费用节约百分比。


* Task Version: researcher@0.2.2


* Generated At: 2026-11-01T17:47:41+08:00


* Role Spec Status: reviewed