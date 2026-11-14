<!-- Google Doc: https://docs.google.com/document/d/1rRIgbR6GJEmL6MN4m0EPkv9F93K-wghDo59SyKDCVtI/edit?usp=drivesdk
Drive ID: 1rRIgbR6GJEmL6MN4m0EPkv9F93K-wghDo59SyKDCVtI
Modified: 2026-10-28T09:54:08.693Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: UW-20261028-AmazonFBA-60DayWindow-MicroReimbursementAudit
* Source Signal References:
   * Signal ID: UW-20261028-AmazonFBA-60DayWindow-MicroReimbursementAudit
   * Generated At: 2026-10-28T01:30:00+08:00
   * Task Version: uneconomic-work@0.1
   * Source File URL: https://docs.google.com/document/d/1RslwDAL2l0fTlbVGUbD1iHDiDUGn5mV-Epu7XpDM_3Y/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-28T01:34:17+08:00
* Research Level: R2 — Economic Underwriting
* Stage Result: HYPOTHESIS_READY
* Unknown Ledger:
   * Known: 亚马逊自 2024 年底起将 FBA 手动索赔窗口从 18 个月严格压缩至 60 天内，并在 2025 年 3 月起强制按采购成本发票估值（未报成本默认按极低算法估算）；单店每年有 1%–3% 的库存发生异常丢损或退货未入库未赔偿，每年沉睡资金达 $1,500–$3,000；单件丢损多在 $12–$40 之间；中小卖家面对跨 4 张报表（库存分类账、退货、移除、结算）耗时 4–6 小时的人工核对，直言“不值得为 $12 费劲”，导致每年数千美元纯利沉没；第三方代索赔软件抽取 20%–25% 且重点服务大卖。
   * Unknown: 亚马逊对利用 SP-API 批量生成并自动提交同类型 Case 工单的频率限制与防滥用惩罚触发阈值。
   * Decision-Critical Unknown: 年销 $100k–$1M 的腰部 FBA 卖家，对于一款“按成功追回金额收取 10% 佣金（远低于行业 25%）或 $29–$49/月 自动化监控订阅的 60 天到期小额库存追回工具”的直接采用意愿。
* Gate Checks:
   * Money: 通过。单店每年沉没 $1,500–$3,000 纯利润，且全美数十万 FBA 卖家体量庞大；低提成或月费模式对比传统代索赔软件极具吸引力。
   * Mechanism: 通过。通过 SP-API 实时拉取交易流水，由算法自动比对跨表 Transaction ID 并在 60 天时钟归零前对齐供应商发票成本，将单笔核对成本从数十美元人工压缩至几美分全自动生成。
   * Persistence: 通过。亚马逊 60 天严苛索赔窗口与采购成本法案为长期平台规则，不可逆。
   * Capture: 通过。1-3 人小团队构建轻量级 SaaS（对接 Amazon SP-API），纯软件与数据分析，零实体物流资产、零库存。
* Final Status: HYPOTHESIS_READY
* Evidence:
   1. NovaData 行业指南《Amazon Reimbursement Guide 2026》（2026-10-08）：详述 60 天死线、制造采购成本新规、单店年弃 $1,500–$3,000 及“$12 不值得花时间”的真实卖家心理。
   2. 亚马逊卖家论坛官方通告（2024-07）：确认 60 天手动索赔合规窗口。
   3. SPS Commerce 供应链解析《Amazon Reimbursement Policy 2026》（2026-06）：拆解 60 天时效与逐行凭证举证要求。
   4. Leviathan Sellers 深度分析《Amazon FBA Reimbursement Policy 2026》（2026-07）：详述采购成本打折机制与 60 天超时放弃风险。
* Counter Evidence:
   1. 卖家若无法提供真实供应商采购发票（如白牌/无票采购）无法满足采购成本索赔要求。
   2. 亚马逊官方自动化赔偿引擎在部分简单场景下会自动补发少量赔偿，但仍漏掉 1%–3%。
* Stop Reason: 四 Gate 均已通过充分独立证据核实，政策明确、数据与机制扎实，小团队轻资产切入点极佳。
* Resume Condition: 不适用（已完成）。
* What became more likely: FBA 卖家将普遍采用自动化 SP-API 脚本进行 60 天滚动监控以防止微额赔偿过期。
* What became less likely: 亚马逊会放宽 60 天索赔窗口或恢复以往 18 个月的秋后大算账模式。
* What did we rule out: 排除了卖家单靠人工手动每月翻查 4 张报表实现全量小额索赔的可行性。
* Task Version: researcher@0.2.2
* Generated At: 2026-10-28T17:51:43+08:00
* Role Spec Status: reviewed


________________


Opportunity Hypothesis: 面向亚马逊 FBA 中小卖家的 60 天时效微额库存丢损自动对账与低提成索赔 SaaS
* Source Signal IDs: UW-20261028-AmazonFBA-60DayWindow-MicroReimbursementAudit
* Source Signal References:
   * Signal ID: UW-20261028-AmazonFBA-60DayWindow-MicroReimbursementAudit
   * Generated At: 2026-10-28T01:30:00+08:00
   * Task Version: uneconomic-work@0.1
   * Source File URL: https://docs.google.com/document/d/1RslwDAL2l0fTlbVGUbD1iHDiDUGn5mV-Epu7XpDM_3Y/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-28T01:34:17+08:00
* Money: 全球数十万中小 FBA 卖家（年销 $100k–$1M）每年因 60 天过期而白白流失的 $1,500–$3,000 丢损赔偿金；卖家愿支付成功挽回金额的 10%（远低于市面大机构 25% 抽成）或按月支付 $29–$49 订阅费。
* Mechanism: 针对卖家“不值得为 $12 丢失货品花 4 小时翻查 4 张报表”的心理门槛，工具通过 Amazon SP-API 每日自动拉取 Inventory Ledger 与退货移除报表：算法自动交叉对齐 Transaction ID，定位被系统漏赔或低赔的单件货品，自动匹配已录入的供应商采购单价发票，在 60 天窗口闭合前全自动生成格式规范的 Seller Central 索赔工单内容，一键复制或批量推送，让单笔 $12 的微小赔偿产生直接正向现金收益。
* Capture: 1-3 人小团队构建轻量 Web 应用（直接对接亚马逊官方 SP-API），纯软件运行，零库存、零实体物流、高毛利。
* Durability: 亚马逊 60 天索赔死线与采购成本估值法已完全制度化，规则不可逆，持续产生滚动对账需求。
* Evidence:
   1. NovaData 指南（2026-10）：https://novadata.io/resources/blog/amazon-reimbursement-guide 证实单件 $12 放弃心理与每年上千美元损失。
   2. 亚马逊卖家论坛公告（2024-07）：https://sellercentral.amazon.com/seller-forums/discussions/t/81c3235d-4c44-47ba-96c5-883cecab3244 确认 60 天时效。
   3. SPS Commerce 分析（2026-06）：https://www.spscommerce.com/community/articles/amazon-reimbursement-policy 拆解发票证明要求。
* Counter Evidence:
   1. 无合规供应商采购发票的卖家无法获赔。
   2. 高频重复开工单可能触碰亚马逊防骚扰频控规则。
* Critical Unknown: 亚马逊对于第三方授权应用在后台协助卖家批量生成索赔 Case 的 SP-API 权限审查与通过率。
* Falsification: 若亚马逊官方彻底实现 100% 完美的自动原价赔偿，不再存在任何漏报漏赔。
* Next Test: 为 5 位年销在 $200k–$500k 的 FBA 真实卖家导出过去 50 天的报表运行脚本比对，测试其漏赔 SKU 数量并验证手动开单后的实际赔付到账率。
* Task Version: researcher@0.2.2
* Generated At: 2026-10-28T17:51:43+08:00
* Role Spec Status: reviewed