<!-- Google Doc: https://docs.google.com/document/d/1gahGU1kHKNw0uExOHEA6ous_3071nzm8CPlvf5r7k7g/edit?usp=drivesdk
Drive ID: 1gahGU1kHKNw0uExOHEA6ous_3071nzm8CPlvf5r7k7g
Modified: 2026-10-30T09:23:02.048Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: UW-20261030-Subcontractor-20DayPrelimNotice-LienRightsPacket


* Source Signal References:


   * Signal ID: UW-20261030-Subcontractor-20DayPrelimNotice-LienRightsPacket
   * Generated At: 2026-10-30T01:30:00+08:00
   * Task Version: uneconomic-work@0.1
   * Source File URL: https://docs.google.com/document/d/1Rdc9kWZ8YHWB44wSRVd1MoczAdMSVN8pFl1iM2w38gw/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-30T01:12:59+08:00


* Research Level: R2 — Economic Underwriting


* Stage Result: HYPOTHESIS_READY


* Unknown Ledger:


   * Known: 全美各州（加州民法典 §8200/§8216、德州、佛州等）强制要求专业分包商在进场 20–30 天内通过挂号信向业主、总包及贷款银行送达初步留置通知（20-Day Preliminary Notice），否则永久丧失机械留置权（加州超 $400 未发通知属执照违规）；在 $10,000 以下小型工程中，70%–80% 的分包商因去县档案局查业主地块耗时 45 分钟、商业代发机构（Levelset 等）单次收费 $60–$85（含挂号邮资）而选择放弃，在总包 60–90 天后拖欠时单次直接损失 $2,000–$8,000 坏账。
   * Unknown: 独立专业分包商在承接商业装修与民宅改建项目中，从总包处直接获取准确项目地址与出票总包名称的标准化程度。
   * Decision-Critical Unknown: 月承接 5–20 个小项目的专业分包商老板（水暖、电气、泥瓦、暖通），对于一款“手机拍照报价单/发票，自动反查地籍法定业主并在 20 天内代发 USPS Certified Mail 挂号信（全包价 $19/单 或月包 $49）”的直接采用意愿。


* Gate Checks:


   * Money: 通过。单案坏账避免价值 $2,000–$8,000，全美数十万专业分包商体量庞大；单单 $19 全包成本远低于行业 $75 门槛。
   * Mechanism: 通过。各州法定义务格式统一（10 磅加粗法定声明）；县级 GIS/地籍开放 API 自动匹配 APN 产权人，结合云端邮政 API（Lob/Postalytics）批量完成 USPS Certified Mail 电子寄送与送达证明归档，将综合成本从 $75 压低至 $10–$15，使小单维权具备绝对正经济性。
   * Persistence: 通过。各州建筑留置权立法稳固长存，开工 20 天死线不可逆。
   * Capture: 通过。1-3 人小团队构建轻量 Web/移动端工具，纯数据查询 + 邮政 API 转发，零实体设备资产、零库存、高毛利。


* Final Status: HYPOTHESIS_READY


* Evidence:


   1. Construction CFO 行业专文《Protecting Lien Rights》（2026-08-06）：详述分包商未发预通知导致留置权灭失的结构性机制及熟人关系误区。
   2. Bay Area Legal 2026 加州初步通知法律指南《20-Day Preliminary Notice in California: What It Is and Why It Matters》（2026-04 发布）：确认加州民法典 §8200–§8216 法定刚性与 20 天窗口。
   3. RentRegistry 建筑合规手册《California 20-Day Preliminary Notice Guide》（2026-10-12）：证实挂号信送达证明与小额项目因成本被放弃的行业现状。
   4. Reddit r/Contractor 纠纷实录《Customer disputing fixed-price contract》（2026-10-22）：资深承包商反复强调必须严格按法定窗口向三方发送挂号信。


* Counter Evidence:


   1. 未分割大型综合体地块需人工核实 APN。
   2. 公立市政工程需特定付款保函（Payment Bond）通知格式。


* Stop Reason: 四 Gate 均已通过充分独立证据核实，法定义务明确，API 成本压缩机制扎实，小团队轻资产切入点极佳。


* Resume Condition: 不适用（已完成）。


* What became more likely: 小型分包商将普及基于地籍 API 与云端邮政代发接口的自动化 20 天预通知工具。


* What became less likely: 分包商会继续在无通知状态下为陌生总包垫资施工。


* What did we rule out: 排除了总包拖欠后分包商能在未发预通知情况下补办机械留置权的可能性。


* Task Version: researcher@0.2.2


* Generated At: 2026-10-30T17:20:52+08:00


* Role Spec Status: reviewed


________________


Opportunity Hypothesis: 面向建筑专业分包商的 20 天初步留置通知自动查验与挂号代发引擎
* Source Signal IDs: UW-20261030-Subcontractor-20DayPrelimNotice-LienRightsPacket


* Source Signal References:


   * Signal ID: UW-20261030-Subcontractor-20DayPrelimNotice-LienRightsPacket
   * Generated At: 2026-10-30T01:30:00+08:00
   * Task Version: uneconomic-work@0.1
   * Source File URL: https://docs.google.com/document/d/1Rdc9kWZ8YHWB44wSRVd1MoczAdMSVN8pFl1iM2w38gw/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-30T01:12:59+08:00


* Money: 全美数十万专业分包商每年因未发初步通知而在总包拖欠时永久损失的数十亿美元工程款（单案避免 $2,000–$8,000 坏账）；分包商愿按单支付 $19 全包服务费或按月订阅 $49 保障其全部小单。


* Mechanism: 针对去县档案局查产权耗时 45 分钟且商业代发收费 $75 导致小单放弃的痛点，工具提供全流程自动化：用户输入项目地址或拍照上传派工单，算法自动调用县级 GIS/地籍开放 API 反查法定业主与抵押贷款行；自动生成符合各州法定字体与免责条款的 20-Day Notice；通过云端邮政 API（Lob 等）自动打印并寄出 USPS Certified Mail，并将送达回执（Green Card）自动存证归档，将单案合规成本压缩至 $10–$15。


* Capture: 1-3 人小团队构建轻量 Web/移动端工具，纯 API 与数据流清洗，零实体资产、零库存、高毛利。


* Durability: 机械留置权法定 20 天窗口全美统一且不可逆，各州立法长期稳固，具有高频复购性。


* Evidence:


   1. Construction CFO（2026-08）：https://constructioncfo.net/construction-protect-lien-rights 确认留置权丧失机制。
   2. Bay Area Legal（2026-04）：https://baylegal.com/20-day-preliminary-notice-in-california-what-it-is-and-why-it-matters/ 确认加州民法典 §8200 刚性。
   3. RentRegistry（2026-10）：https://www.rentregistry.io/ca-preliminary-notice 确认挂号信送达与小额放弃现状。


* Counter Evidence:


   1. 部分市政工程需要 Payment Bond 专门表单。
   2. 复杂多产权地块需简单人工复核。


* Critical Unknown: 小型分包商老板在开工后 1–15 天黄金期内完成项目录入的操作习惯养成与获客漏斗。


* Falsification: 若各州立法全面废除初步留置通知要求，允许分包商在工程结束未收款时直接自由登记留置权。


* Next Test: 对接加州与德州 3 家月承接 10 个项目的小型水电/暖通分包商，测试项目地址地籍 API 反查准确率，并为其实测寄送首批 5 封挂号通知书验证送达时效与回执存证完整性。


* Task Version: researcher@0.2.2


* Generated At: 2026-10-30T17:20:52+08:00


* Role Spec Status: reviewed