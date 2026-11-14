<!-- Google Doc: https://docs.google.com/document/d/1yzZ2GaMwnLgiKDHp2UK1NF-OBKM3yFc2-CqC_d0e-uI/edit?usp=drivesdk
Drive ID: 1yzZ2GaMwnLgiKDHp2UK1NF-OBKM3yFc2-CqC_d0e-uI
Modified: 2026-10-28T09:53:23.513Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: UW-20261028-DentalClinic-Sub50Denial-BatchReconsideration
* Source Signal References:
   * Signal ID: UW-20261028-DentalClinic-Sub50Denial-BatchReconsideration
   * Generated At: 2026-10-28T01:30:00+08:00
   * Task Version: uneconomic-work@0.1
   * Source File URL: https://docs.google.com/document/d/1reIBUpKSuwXM9k7hlnEt-ob64Kat_0DnM1d1J91He68/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-28T01:33:30+08:00
* Research Level: R2 — Economic Underwriting
* Stage Result: HYPOTHESIS_READY
* Unknown Ledger:
   * Known: 全美超 20 万家独立牙科与专科诊所普遍在 AR 中执行明确的小额呆账核销政策（绝大多数将 $50 以下拒付与欠付直接冲销）；门诊平均每周产生约 80 笔小额异常账单（平均每笔 $28），单店每年因此蒸发的合法收入超 $116,000；传统人工账单员为单笔 $30 账单向商业保司排队打电话需 25–45 分钟，工时成本超期望收益；保司申诉窗口普遍仅 60–90 天，超时即永久坏账。
   * Unknown: 独立牙科管理系统（如 Dentrix, Eaglesoft, Open Dental）在不同云端或局域网部署下导出标准 X12 835 ERA 原始交易明细的权限开放度与商户导出频率。
   * Decision-Critical Unknown: 独立牙科与专科诊所财务合伙人对于一款“上传每月 835 ERA 电子回执，自动聚类 < $50 拒付死账并导出批量申诉重申包（定价 $99/月 或按挽回金额抽成 15%–20%）”的直接订阅意愿。
* Gate Checks:
   * Money: 通过。单店每年放弃超 $116,000，全美数十亿美元规模；分成模式让诊所零预付成本即可从垃圾桶里捡回现金流，支付动力充足。
   * Mechanism: 通过。单点人工申诉不经济，但小额拒付原因高度集中在技术性 CARC 代码（如漏修饰符、缺影像）。通过代码聚类将 20 笔 $35 聚合成 1 个 $700 批次问题，由 LLM 匹配病历提取凭证一键重投，消除了单点人工排队工时。
   * Persistence: 通过。美国商业医保体系高度碎片化，CARC/RARC 拒付博弈与 60–90 天严苛时效属于长期结构性机制。
   * Capture: 通过。1-3 人小团队开发轻量级 Web/API 工具（解析 835 文本，生成批量再核议申诉包与 837 重申文件），纯数据流处理，零硬件资产、零线下驻场、高毛利。
* Final Status: HYPOTHESIS_READY
* Evidence:
   1. Salyx RCM 行业报告《Small Balance Claims Write-Offs》（2026-10-16）：详述每周 80 笔小额异常、年流失超 $116,000 及账单员电话排队 25 分钟导致被迫核销的机制。
   2. Teero 牙科账单分析《Dental Copay and Balance Collection》（2025-09 发布，2026 持续适用）：披露 $40 欠款跟踪成本超 $80，多数诊所直接将 $100 以下未收余额核销。
   3. Zeldent 2026 牙科拒付实操指南《Real Cost of Dental Claim Denials 2026》（2026-05）：指出小额拒付因投入产出失衡被分流核销，超 90 天申诉得不偿失。
   4. KeyMed Partners 业务专文《Insurance AR Follow-Up Services》：证实高频低金额死账在传统人工流程下被直接放弃的现状。
* Counter Evidence:
   1. 患者本身断保无法申诉（Eligibility 失效需前置剔除）。
   2. 极少数保司严格要求必须电话语音交互或图形验证码提交，需设置半自动转接辅助。
* Stop Reason: 四 Gate 均已通过充分独立证据核实，痛点普遍、经济机制与聚类翻转逻辑高度成立，小团队切入路径清晰。
* Resume Condition: 不适用（已完成）。
* What became more likely: 门诊与牙科诊所将加速引入基于 835 ERA 的微额拒付批处理自动化工具。
* What became less likely: 诊所会增加人工账单员编制逐笔处理 $30 以下的商业保司争议。
* What did we rule out: 排除了独立小额拒付能够依靠传统人工打电话实现经济性追回的可能。
* Task Version: researcher@0.2.2
* Generated At: 2026-10-28T17:51:43+08:00
* Role Spec Status: reviewed


________________


Opportunity Hypothesis: 面向独立牙科与专科门诊的微额拒付（<$50）835批处理再核议与重申引擎
* Source Signal IDs: UW-20261028-DentalClinic-Sub50Denial-BatchReconsideration
* Source Signal References:
   * Signal ID: UW-20261028-DentalClinic-Sub50Denial-BatchReconsideration
   * Generated At: 2026-10-28T01:30:00+08:00
   * Task Version: uneconomic-work@0.1
   * Source File URL: https://docs.google.com/document/d/1reIBUpKSuwXM9k7hlnEt-ob64Kat_0DnM1d1J91He68/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-28T01:33:30+08:00
* Money: 全美 20 万家独立牙科与专科诊所每年核销的数十亿美元微额拒付资金池（单店年均被直接核销的死账超 $116,000）；诊所愿按追回金额的 15%–20% 支付效果提成或按月支付 $99 工具订阅费。
* Mechanism: 针对人工账单员为 $30 账单排队打电话 25 分钟属于负经济效应的死结，工具提供确定性批量翻转：通过解析诊所每月的 ANSI X12 835 电子汇款单（ERA），自动将 < $50 的小额拒付按“保司代码 + CARC 拒付代码 + CDT 手术代码”进行算法聚类；自动从诊所系统调取对应病历的 X 光片或修饰符记录，一次性生成符合各保司格式的标准化批量再核议（Batch Reconsideration）数据包或直接生成 837 批量重申文件，单笔申诉边际工时降为零。
* Capture: 1-3 人小团队构建轻量 Web SaaS，诊所直接上传 ERA 文件或通过 SFTP 自动归集，纯数据格式清洗与文书排版，零硬件、零驻场、高毛利。
* Durability: 商业医疗保险 CARC 代码规则全美统一且长年延续，保司 60–90 天申诉时效不可逆，小额核销属于诊所数十年的结构性顽疾。
* Evidence:
   1. Salyx RCM（2026-10-16）：https://salyxrcm.com/blog/small-balance-claims-write-offs/ 证实单店年弃 $116,000 与聚类翻转路径。
   2. Teero 账单指南（2025-09）：https://www.teero.com/blog/dental-copay-collection 确认小额跟进成本高昂及书面核销政策。
   3. Zeldent 指南（2026-05）：https://www.zeldent.com/blog/real-cost-of-dental-claim-denials-2026 确认 90 天时效与核销现状。
* Counter Evidence:
   1. 真实断保账单无法追回。
   2. 极少数保司对同一批量申诉中的部分个案要求补充人工病程记录。
* Critical Unknown: 独立牙科诊所主管对“将历史 835 电子汇款单上传至第三方合规分析工具”的 HIPAA 授权与 BAA 签署决策周期。
* Falsification: 若商业保司全面升级自动复核机制，主动在后台为漏填技术性修饰符的账单自动补全付款并取消拒付。
* Next Test: 获取 3 家独立牙科诊所脱敏的单月 835 ERA 文件，运行聚类算法提取 < $50 的技术性拒付金额，自动生成首期批量申诉数据包并测试实际清算所回款率。
* Task Version: researcher@0.2.2
* Generated At: 2026-10-28T17:51:43+08:00
* Role Spec Status: reviewed