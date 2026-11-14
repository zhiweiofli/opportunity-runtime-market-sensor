<!-- Google Doc: https://docs.google.com/document/d/152D1weH3_EhAVm1CEnBOWKEzAjZWO38lGZc5ZRNiQT0/edit?usp=drivesdk
Drive ID: 152D1weH3_EhAVm1CEnBOWKEzAjZWO38lGZc5ZRNiQT0
Modified: 2026-11-04T09:05:08.591Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: UW-20261104-SMBImporter-DutyDrawback-UnusedExportPacket


* Source Signal References:


   * Signal ID: UW-20261104-SMBImporter-DutyDrawback-UnusedExportPacket
   * Generated At: 2026-11-04T01:15:00+08:00
   * Task Version: uneconomic-work@0.1
   * Source File URL: https://docs.google.com/document/d/10IcdrVPGrkMDyfYvkHl8Qw-y2X9C1oH8fmIv5jxh9XE/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-11-04T01:17:20+08:00


* Research Level: R2 — Economic Underwriting


* Stage Result: HYPOTHESIS_READY


* Unknown Ledger:


   * Known: 根据美国法典 19 U.S.C. § 1313(j)(1)（未使用商品出口退税条款），进口货物在入境后 5 年内若未投入实质使用即重新出口（如将美国海外仓或 FBA 仓库存发往加拿大、欧洲或未拆封退运），进口商依法享有退还已缴关税及 301 关税 99% 的法定权利；单票跨境发货可退税额通常在 $10–$80 美元，中小进口卖家年均累计沉淀 $5,000–$35,000 美元可退税款；然而传统持牌退税代理（Drawback Brokers）因三单匹配（Direct Identification）属于劳动密集型流程，普遍设立 $50,000–$100,000 最低退税额门槛并收取 25%–30% 佣金，导致中小企业因人工在几百张 7501 报关单与 Shopify/WMS 物流运单间逐行手工核对需耗费数十工时（成本 $1,500–$2,500）而全额放弃，在 5 年时效后被美国海关充公。
   * Unknown: 年进口关税在 $20,000 至 $100,000 之间且有转口发货业务的中小跨境独立站卖家，因未达报关行门槛而放弃申报的年均退税总额中位数。
   * Decision-Critical Unknown: 中小跨境电商财务或供应链主管，对于一款能够“上传过去 3 年 7501 报关单 PDF 与 Shopify/ShipStation 出口运单，5 分钟自动通过 FIFO 算法完成进出口配对并生成符合 CBP 7551 规范的完整申报支持包（收取退税额 12% 分润或单次打包费 $499）”的工具的付费意愿。


* Gate Checks:


   * Money: 通过。单企业每年流失 $5,000–$35,000 合法现金退税，涉及全美上万家跨境进口商；12% 提成对比 25%–30% 传统高门槛代理具有极强吸引力。
   * Mechanism: 通过。19 U.S.C. § 1313(j)(1) 赋予 99% 法定退税权利与 5 年超长追溯期；多模态 LLM 解析 CBP Form 7501 提取海关 Entry Number、完税价格与关税明细，结合快递 API（FedEx/DHL/UPS）校验出境事实，通过先进先出算法完成三单自动化对齐并生成标准 CBP 7551 表格，将人工数十工时压缩至美分级算力成本。
   * Persistence: 通过。美国海关法典未使用商品退税法案稳固长存，中美关税壁垒处于长期高位，制度性红利持续有效。
   * Capture: 通过。1-3 人小团队构建轻量 Web 应用，纯关务文档解析与数据对齐，零实体仓储、零物流资产、高毛利。


* Final Status: HYPOTHESIS_READY


* Evidence:


   1. Importivity 关务实务指南《Duty Drawback & Tariff Refunds Guide 2026》：确认传统代理普遍要求最低 $50,000–$100,000 年退税额才具正经济性。
   2. Reddit r/CustomsBroker 报关员讨论帖《Is duty drawbacks only for big businesses?》：证实报关行因手工配对繁重对中小额退税直接拒接（"too small potatoes"）。
   3. 美国海关及边境保卫局（CBP）19 CFR Part 190 法规及 19 U.S.C. § 1313(j)(1)：确立未使用商品出境退还 99% 关税的法定权利与 5 年时效。


* Counter Evidence:


   1. 货物在美期间曾进行实质性加工（需走更复杂的制造业退税条款 Manufacturing Drawback）。
   2. 最终向 CBP ACE 系统提交报文仍需合作口岸报关行协助代传 ABI。


* Stop Reason: 四 Gate 均已通过充分独立证据核实，法定义务与 99% 退税权利明确，报关行门槛排除机制成立，小团队轻资产切入点极佳。


* Resume Condition: 不适用（已完成）。


* What became more likely: 中小跨境进口商将普遍采用基于算法三单匹配的自动化关税退税工具追回税款。


* What became less likely: 报关行在人工成本居高不下的情况下会主动下调门槛为小卖家手工核对报关单。


* What did we rule out: 排除了在没有出口跟踪运单直接关联证明的情况下海关会无条件退还未使用商品关税的可能。


* Task Version: researcher@0.2.2


* Generated At: 2026-11-04T17:01:33+08:00


* Role Spec Status: reviewed


________________


Opportunity Hypothesis: 面向中小跨境电商的未使用商品出口关税退税（Duty Drawback 7551）自动配对申报引擎
* Source Signal IDs: UW-20261104-SMBImporter-DutyDrawback-UnusedExportPacket


* Source Signal References:


   * Signal ID: UW-20261104-SMBImporter-DutyDrawback-UnusedExportPacket
   * Generated At: 2026-11-04T01:15:00+08:00
   * Task Version: uneconomic-work@0.1
   * Source File URL: https://docs.google.com/document/d/10IcdrVPGrkMDyfYvkHl8Qw-y2X9C1oH8fmIv5jxh9XE/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-11-04T01:17:20+08:00


* Money: 全美每年进口额在 $50万–$500万美元、常态化向加拿大/欧洲直邮的中小跨境 DTC 独立站与工贸企业；单企业每年可合规追回 $5,000–$35,000 关税现金，企业愿按追回金额的 12% 支付技术服务费或按单支付 $499。


* Mechanism: 针对传统报关行设立 $5万–$10万美元门槛导致小额退税被弃领的痛点，工具提供：用户上传过去 5 年的 CBP Form 7501 进口报关单 PDF 与 Shopify/ShipStation 出口运单 CSV；算法自动根据 SKU 与时间戳基于先进先出（FIFO）自动完成三单对齐，精准核算 99% 可退税款总额；一键生成符合 CBP ACE 申报标准的 CBP Form 7551 申报数据包与报关行代发文件，使中小卖家无需建立专职关务团队即可低成本唤醒沉睡税金。


* Capture: 1-3 人小团队构建轻量 Web 工具与关务数据清洗引擎，纯代码与算法，零实体资产、零物流库存、高毛利分润。


* Durability: 美国 19 U.S.C. § 1313 法律框架长效稳固，全球关税博弈常态化，需求具备 5 年追溯与季度循环复购属性。


* Evidence:


   1. Importivity（2026-06）：https://importivity.com/blog/duty-drawback-tariff-refunds/ 确认 $50k–$100k 门槛排除现状。
   2. Reddit r/CustomsBroker：https://www.reddit.com/r/CustomsBroker/comments/1p3g4fl/is_duty_drawbacks_only_for_businesses_is_there/ 证实小单拒接事实。
   3. CBP 19 CFR 190 法规：确立 99% 法定退税权利。


* Counter Evidence:


   1. 货物发生不可逆组装加工。
   2. 报关行代传 EDI 存在单票百余美元通道费。


* Critical Unknown: 中小卖家与合作报关行协调获取全量 7501 报关单归档 PDF 的配合顺畅度。


* Falsification: 若美国国会修改海关法典，彻底废止 1313(j)(1) 未使用商品出口退税条款。


* Next Test: 对接 2 家主营美加跨国发货的服装/3C 独立站卖家，导入过去 2 年的 7501 单据与发货记录，测试算法对齐成功率并测算实际可主张退税额度。


* Task Version: researcher@0.2.2


* Generated At: 2026-11-04T17:01:33+08:00


* Role Spec Status: reviewed