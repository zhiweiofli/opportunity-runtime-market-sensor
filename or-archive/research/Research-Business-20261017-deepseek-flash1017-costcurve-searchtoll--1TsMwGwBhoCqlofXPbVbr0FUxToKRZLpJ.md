<!-- Google Doc: https://drive.google.com/file/d/1TsMwGwBhoCqlofXPbVbr0FUxToKRZLpJ/view?usp=drivesdk
Drive ID: 1TsMwGwBhoCqlofXPbVbr0FUxToKRZLpJ
Modified: 2026-10-22T09:44:47.238Z
Mirrored At: 2026-11-14 +08:00
-->

# Opportunity Runtime Research Record

- **Source Signal IDs**: Business-20261017-deepseek-flash1017-costcurve-searchtoll
- **Source Signal References**:
  - Signal ID: Business-20261017-deepseek-flash1017-costcurve-searchtoll
  - Generated At: 2026-10-22T09:09:50+08:00
  - Task Version: business-sensor@0.2.1
  - Source File URL: https://docs.google.com/document/d/1ThMaGiZbuVSCFGmwGT_BqQZ6iF02f6SLJ5iMxIY_RIo/edit?usp=drivesdk&ouid=101589702958564347595
  - Source File Modified At: 2026-10-22T09:12:23+08:00
- **Research Level**: R2 — Economic Underwriting
- **Stage Result**: HYPOTHESIS_READY
- **Unknown Ledger**:
  - Known: DeepSeek 于 2026-10-17 官方以 MIT 协议开源 V4.1-Flash-1017 模型权重，API 定价输入 $0.15 / 输出 $0.60 每百万 tokens（缓存读取 $0.003/M tokens）；DeepSWE 跑分达 77.0（单任务成本折合约 $0.016，较 GPT-6.1 的 $0.058 降低 3.6 倍）；官方同步上线 Search API 与 Fetch API（公开牌价 $0.75 / 1,000 次请求，限制 5 QPS），并明确将于 2026年11月1日 终结外部智能体（Harness / Claude Code / Codex）集成的免费试用期，转为正式按量扣费。
  - Unknown: 11 月 1 日正式扣费后，开源智能体开发者对 DeepSeek 原生 Search API 的付费留存率与调用频次分布；DeepSeek Search API 在垂直专业技术文档上的检索质量相比 Brave Search / Tavily 的实际劣势幅度。
  - Decision-Critical Unknown: 中小型研发团队在面临 $0.75/1k 外部检索账单时，对于能够拦截 40%~60% 冗余搜索与文档重复抓取的轻量级 Agentic Search Cache 网关的月费采购意愿（如 $19~$49/月）。
- **Gate Checks**:
  - Money: 通过。全球使用开源与闭源智能体开展代码自动化、数据分析的企业直接产生 API 推理与外部搜索通道硬支出；Search API 每千次 $0.75 为确定性收费，底层推理单任务降至 $0.016 创造了极大的软件毛利空间。
  - Mechanism: 通过。双重机制叠加：1) Cost Curve Shift：极限压低代码修复与自动化工程的单位任务边际算力成本，将此前昂贵的人工或闭源模型外包转为 85%+ 毛利的微型 SaaS；2) New Toll Booth：智能体在多轮迭代中频繁查询相同网页/API 文档，引入本地语义去重与检索缓存中间件可直接为企业削减 50% 搜索通道账单。
  - Persistence: 通过。模型权重基于 MIT 协议永久开源，KV 缓存压缩架构具有物理确定性；Search API 牌价已作为官方商业条款发布，商业收费不可逆。
  - Capture: 通过。1-3 人小团队可构建纯 API/Webhook 驱动的“智能体搜索去噪与文档缓存网关（Agentic Search Proxy）”或“基于 Flash-1017 的轻量交钥匙代码审查与单元测试补全 Bot”，无需自建重算力，纯软件交付，零重资产。
- **Final Status**: HYPOTHESIS_READY
- **Evidence**:
  1. AI Weekly 深度快讯《[DeepSeek Opens V4.1-Flash-1017 Weights and $0.75 Search API](https://aiweekly.co/alerts/deepseek-opens-v41-flash-1017-weights-and-075-search-api)》（2026-10-17 发布）：详述官方 $0.15/$0.60 价格、MIT 权重开源、Search API $0.75/1k 价目及 11 月 1 日计费生效节点，引用 56 组测试数据证实单任务成本降至 $0.016。
  2. OpenRouter 官方模型卡与定价路由《[DeepSeek V4.1 Flash 1017 - API Pricing & Benchmarks](https://openrouter.ai/deepseek/deepseek-v4.1-flash-1017)》（2026-10-17）：公布官方牌价与实测基准，记录 DeepSWE 得分为 77.0。
  3. DeepSeek API 官方文档《[Search & Fetch](https://api-docs.deepseek.com/guides/search)》（2026-10 最新更新）：正式披露 Search 与 Fetch 商业接口技术规范与参数。
- **Counter Evidence**:
  1. 并发与质量限制：Search API 具有 5 QPS 初始限速，且检索质量与抓取广度相较于成熟商业引擎（如 Google / Bing）存在差距。
  2. 替代竞品充分：市场已有 Brave Search API、Tavily、Serper 等成熟搜索代理工具，单价多在 $0.50~$2.00/1k，小团队网关需兼容多提供商以防单点锁定。
- **Stop Reason**: 四 Gate（Money, Mechanism, Persistence, Capture）均已通过充分独立证据核实，痛点与机制坚实，反证已被评估，已具备开展下一步原型验证的完整条件。
- **Resume Condition**: 不适用（已完成）。
- **What became more likely**: 更多自主代码智能体与本地研发助理将全面采用 Flash-1017 作为主力执行模型，同时外部网页检索调用将受到更严格的本地缓存与成本治理。
- **What became less likely**: 闭源头部大模型能维持针对代码自动化场景每百万 Token 数美元的高溢价。
- **What did we rule out**: 排除了 DeepSeek Search API 会无限期免费开放的假设。
- **Task Version**: researcher@0.2.2
- **Generated At**: 2026-10-22T17:42:35+08:00
- **Role Spec Status**: reviewed

---

## Opportunity Hypothesis: 面向开源编码智能体的 Search API 语义缓存与成本优化网关

- **Source Signal IDs**: Business-20261017-deepseek-flash1017-costcurve-searchtoll
- **Source Signal References**:
  - Signal ID: Business-20261017-deepseek-flash1017-costcurve-searchtoll
  - Generated At: 2026-10-22T09:09:50+08:00
  - Task Version: business-sensor@0.2.1
  - Source File URL: https://docs.google.com/document/d/1ThMaGiZbuVSCFGmwGT_BqQZ6iF02f6SLJ5iMxIY_RIo/edit?usp=drivesdk&ouid=101589702958564347595
  - Source File Modified At: 2026-10-22T09:12:23+08:00
- **Money**: 研发团队每月数百至数千美元的智能体外部 Web Search API（DeepSeek $0.75/1k、Tavily $1.00/1k）通道预算；团队愿支付节省通道费的 20%~30% 作为网关订阅费。
- **Mechanism**: 智能体（如 Claude Code、Cursor、DeepSeek Harness）在排查 Bug、查询第三方库语法或抓取框架文档时，多轮对话中存在高达 50% 以上的相似/重复 URL 抓取与查询；网关在本地实现轻量语义哈希去重与 Markdown 缓存，单次请求命中缓存直接返回，杜绝重复收费。
- **Capture**: 1-3 人小团队构建开源/托管双模的轻量 HTTP/REST 代理网关，直接作为 `DEEPSEEK_SEARCH_BASE_URL` 替换原生端点，零重资产、零重售后。
- **Durability**: 智能体自主调用外部知识具有长期必然性，且模型厂商对 Search API 的按次计量商业化不可逆。
- **Evidence**:
  1. AI Weekly 深度快讯（2026-10-17）：https://aiweekly.co/alerts/deepseek-opens-v41-flash-1017-weights-and-075-search-api 证实 Search API 商业化及 11 月 1 日计费。
  2. OpenRouter 官方定价（2026-10-17）：https://openrouter.ai/deepseek/deepseek-v4.1-flash-1017 证实 DeepSWE 77.0 及极低 Token 成本。
  3. DeepSeek 官方指南（2026-10）：https://api-docs.deepseek.com/guides/search 披露 Search/Fetch 规范。
- **Counter Evidence**:
  1. 开发者可在代码中自行编写简单字典缓存，通用开源库可能削弱商业托管版价值。
  2. 搜索结果时效性敏感，过期缓存可能误导智能体生成过时代码。
- **Critical Unknown**: 典型研发团队使用智能体日常开发时，搜索查询的重复命中率（Cache Hit Rate）与开发者对缓存失效（TTL）容忍度的平衡点。
- **Falsification**: 若实际生产环境中智能体发起的搜索请求高度发散且几乎无重合（命中率低于 15%），使得缓存网关带来的实际成本节约微乎其微。
- **Next Test**: 构建一个极简的本地 Search Cache Proxy 原型，嵌入 3 个真实开发者的日常 Claude Code / DeepSeek Harness 工作流测试 1 周，统计真实搜索请求去重率与账单节省幅度。
- **Task Version**: researcher@0.2.2
- **Generated At**: 2026-10-22T17:42:35+08:00
- **Role Spec Status**: reviewed
