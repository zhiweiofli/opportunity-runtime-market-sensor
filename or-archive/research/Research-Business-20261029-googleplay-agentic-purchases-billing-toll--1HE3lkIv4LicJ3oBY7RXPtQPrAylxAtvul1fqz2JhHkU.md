<!-- Google Doc: https://docs.google.com/document/d/1HE3lkIv4LicJ3oBY7RXPtQPrAylxAtvul1fqz2JhHkU/edit?usp=drivesdk
Drive ID: 1HE3lkIv4LicJ3oBY7RXPtQPrAylxAtvul1fqz2JhHkU
Modified: 2026-10-30T09:24:16.638Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: Business-20261029-googleplay-agentic-purchases-billing-toll


* Source Signal References:


   * Signal ID: Business-20261029-googleplay-agentic-purchases-billing-toll
   * Generated At: 2026-10-30T09:54:18+08:00
   * Task Version: business-sensor@0.2.1
   * Source File URL: https://docs.google.com/document/d/1xuREdeXxdbUWt2RMNKSzpUnR6_nGk-XfKDigHtRqGuw/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-30T09:57:56+08:00


* Research Level: R2 — Economic Underwriting


* Stage Result: HYPOTHESIS_READY


* Unknown Ledger:


   * Known: 2026年10月29日 Google 官方发布开发者政策重大更新：1）支付政策（Payments Policy）正式显式延伸并强制覆盖至所有 AI 与智能体购买体验（AI or Agentic Experiences），规定任何由 AI 智能体或对话交互促成的数字商品与订阅购买必须强制走 Google Play 结算系统（15%–30% 平台抽成），封死外部网页外链或无头结算绕道；2）AppFunctions API（基于 MCP 协议将 Android 移动应用功能暴露给 Gemini 与第三方 Agent 的架构）正式纳入严格审核，明令禁止 AppFunctions 欺骗或操纵智能体、绕过安全控制或在系统背后静默诱导交易；开发者享有 30 天合规缓冲期。
   * Unknown: 开发者在 AppFunctions 体系中通过外部自建 Agent 间接提供云端生成式算力服务时，Google Play 审核团队对于“纯应用内数字商品（强制 Play 结算）”与“B2B 企业服务算力（允许第三方外部开票）”的界定自由裁量权尺度。
   * Decision-Critical Unknown: 准备将移动应用能力通过 AppFunctions/MCP 暴露给 Gemini 及第三方智能体变现的中小型 Android 开发者，对于一款“提供符合 Google Play 政策的 Agentic In-App Billing 桥接 SDK 及 AppFunctions 操纵漏洞静态扫描审计工具（定价 $29–$99/月）”的直接采购意愿。


* Gate Checks:


   * Money: 通过。涉及全球数十亿 Android 设备每年上千亿美元的应用内购买与订阅流水；智能体交互强推 Google Play Billing（15%–30% 抽成），违规面临全网下架与封号，开发者具备生死攸关的合规采购预算。
   * Mechanism: 通过。商业收费站（New Toll Booth）与防操纵政策卡点：从传统人机点击转向 Agentic 交互，Google 官方在移动商业新范式上确立排他性抽税权；轻量 SDK 将智能体意图（Intent）转化为符合 Play 规范的 A2UI 购买确认弹窗与合规回调，在技术上具有极强的规范确定性。
   * Persistence: 通过。Google Play 官方正式开发者政策发布，已进入 30 天强制倒计时，属于不可逆的底层移动商业治理规则。
   * Capture: 通过。1-3 人小团队构建轻量 Android 客户端合规 SDK 与 CI/CD 静态扫描插件（AppFunctions Policy Linter），纯代码与 API 交付，零实体资产、零硬件、高毛利。


* Final Status: HYPOTHESIS_READY


* Evidence:


   1. Google Play Console 开发者政策官方公告《Policy announcement: October 29, 2026》（2026-10-29）：官方明确规定支付政策延伸至 AI/Agentic experiences，AppFunctions 严格禁止操纵智能体，强制 30 天合规期。
   2. Google Play Console Help 官方公告汇总《Announcements - Play Console Help》（2026-10-29）：确认核心政策合规时间表与审核申报入口。
   3. The Decoder 深度报道《Google opens Android development to third-party AI agents and unveils new Gemini APIs》（2026-10-28）：详述 Android Dev Summit 发布 AppFunctions、Connected Apps Platform 与 MCP 架构，揭示当应用具备交易属性时的严苛支付合规要求。


* Counter Evidence:


   1. 超大型移动巨头（如 Netflix、Spotify）通过法律与反垄断诉讼谋求专属例外。
   2. 纯免费开源应用不涉及任何数字交易，无需接入支付桥接。


* Stop Reason: 四 Gate 均已通过充分独立证据核实，政策确定、平台强制抽税卡点明确，小团队轻资产切入点极佳。


* Resume Condition: 不适用（已完成）。


* What became more likely: Android 开发者在将应用功能包装为 Agentic AppFunctions 时，将普遍集成标准化的 A2UI 购买确认与 Play Billing 桥接层。


* What became less likely: 开发者能继续利用对话式 AI 或无头智能体神不知鬼不觉地引导用户走外部网页结账通道。


* What did we rule out: 排除了在 10月29日 政策生效后 Google 会放任智能体在 Android 系统内进行免 15%–30% 抽成的第三方数字购买。


* Task Version: researcher@0.2.2


* Generated At: 2026-10-30T17:20:52+08:00


* Role Spec Status: reviewed


________________


Opportunity Hypothesis: 面向 Android 开发者的 Agentic In-App Billing 桥接 SDK 与 AppFunctions 政策合规审计工具
* Source Signal IDs: Business-20261029-googleplay-agentic-purchases-billing-toll


* Source Signal References:


   * Signal ID: Business-20261029-googleplay-agentic-purchases-billing-toll
   * Generated At: 2026-10-30T09:54:18+08:00
   * Task Version: business-sensor@0.2.1
   * Source File URL: https://docs.google.com/document/d/1xuREdeXxdbUWt2RMNKSzpUnR6_nGk-XfKDigHtRqGuw/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-30T09:57:56+08:00


* Money: 全球数百万在 Google Play 上分发数字内容与生成式 AI 服务的应用开发者预算；开发者愿为杜绝封店下架风险并快速支持 Agentic 购买，按月支付 $29–$99 订阅合规中间件 SDK 与 CI 扫描工具。


* Mechanism: 针对 Google Play 10月29日 新规强制要求所有智能体促成的购买走 Play 结算并明令禁止操纵 Agent 的痛点，工具提供：1）轻量级 Kotlin/Java SDK，将 Gemini/外部智能体调用的 AppFunctions Purchase Intent 自动安全编译为符合 Google 政策的 Agent-to-UI (A2UI) 显式确认卡片，直连底层 Google Play Billing 回调；2）静态代码与 Prompt 检查器（AppFunctions Policy Linter），在 CI/CD 流水线中扫描函数元数据，提前拦截潜在的智能体误导或绕过风险。


* Capture: 1-3 人小团队构建开源核心 SDK + 商业版合规监控云后台，纯移动端代码与开发者服务，零硬件、零库存、高毛利。


* Durability: Google Play 政策长期强制生效，移动端 AI 智能体与 AppFunctions 深度整合属于下一代移动生态长期趋势。


* Evidence:


   1. Google Play Console 政策通告（2026-10-29）：https://support.google.com/googleplay/android-developer/answer/18100766 确立支付延伸与 AppFunctions 防操纵规则。
   2. Play Console Help（2026-10-29）：https://support.google.com/googleplay/android-developer/announcements/13412212?hl=en 确认 30 天合规窗口。
   3. The Decoder 深度分析（2026-10-28）：https://the-decoder.com/google-opens-android-development-to-third-party-ai-agents-and-unveils-new-gemini-apis/ 拆解 Android 智能体商业化生态。


* Counter Evidence:


   1. 具备庞大合规法务与工程团队的顶级开发商自行编写 A2UI 弹窗。
   2. 纯离线或广告变现类应用不受支付政策约束。


* Critical Unknown: Google Play Console 官方审核机器人对 AppFunctions 函数元数据与 Prompt 上下文的自动化审查算法与误杀拦截率。


* Falsification: 若欧盟或反垄断法院裁定 Google 强制对第三方外部智能体促成的购买征收 15%–30% Play 抽税属于非法垄断并予以叫停。


* Next Test: 开发一套支持 Gemini AppFunctions 的开源 Kotlin 支付桥接原型库，在 Google Play Internal Track 上架一款接入该库的测试 AI 应用，验证在 30 天新政下提交审核的通过率与 A2UI 购买流畅度。


* Task Version: researcher@0.2.2


* Generated At: 2026-10-30T17:20:52+08:00


* Role Spec Status: reviewed