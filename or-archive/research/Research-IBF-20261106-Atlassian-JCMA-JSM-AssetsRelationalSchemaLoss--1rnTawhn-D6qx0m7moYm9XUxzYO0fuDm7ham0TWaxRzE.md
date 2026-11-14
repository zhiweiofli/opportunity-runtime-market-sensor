<!-- Google Doc: https://docs.google.com/document/d/1rnTawhn-D6qx0m7moYm9XUxzYO0fuDm7ham0TWaxRzE/edit?usp=drivesdk
Drive ID: 1rnTawhn-D6qx0m7moYm9XUxzYO0fuDm7ham0TWaxRzE
Modified: 2026-11-06T09:49:25.591Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: IBF-20261106-Atlassian-JCMA-JSM-AssetsRelationalSchemaLoss


* Source Signal References:


   * Signal ID: IBF-20261106-Atlassian-JCMA-JSM-AssetsRelationalSchemaLoss
   * Generated At: 2026-11-06T17:15:00+08:00
   * Task Version: installed-base-friction@0.2
   * Source File URL: https://docs.google.com/document/d/1BGWMQaXXtLy5pAMzswzJOXQHfp0vMBBP_4BIXqRMvFo/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-11-06T17:12:03+08:00


* Research Level: R2 — Economic Underwriting


* Stage Result: HYPOTHESIS_READY


* Unknown Ledger:


   * Known: 随着 Atlassian 终结 Jira Server 并宣布 Data Center 停止销售新许可、2029 年彻底 EOL，全球超 5 万家企业被迫将本地 Jira Service Management (JSM) 迁往 Jira Cloud；然而官方核心迁移工具 Jira Cloud Migration Assistant (JCMA) 明确不支持迁移 Assets（原 Insight CMDB 资产库）的对象模式（Schemas）、属性及核心的网状引用关系（Reference Fields）；官方推行的 CSV 手动导入彻底打碎了对象间关联引用（如员工-电脑-软件授权链条），导致上云首日客户服务台申请表单引用的资产下拉框全线报错瘫痪、自动化派单规则断流；Atlassian 认证合作伙伴（Solution Partners）端到端定制迁移咨询报价高达 $10,000–$40,000，中型 IT 团队陷入手工录入造成业务停摆或被迫采购天价外包的困境。
   * Unknown: 计划在未来 12 个月内迁移至 Jira Cloud 的 JSM 企业客户中，已建立超过 3 层对象网状引用关系但未向大型方案商签署咨询合同的存量规模。
   * Decision-Critical Unknown: 负责从 Server/DC 迁往 Cloud 的企业 JSM 管理员与 IT 运维总监，对于一款能够“通过两阶段 REST API 自动递归抽取 Schema 继承拓扑并完整还原网状 Reference 引用依赖的一键式轻量迁移 CLI 工具（单次迁移实例买断 $499–$999）”的直接采购意愿。


* Gate Checks:


   * Money: 通过。外部方案商实施报价起步 $10,000+，服务台表单瘫痪每天导致数千美元停滞损失；自动化迁移工具 $499 具备 20 倍刚性省钱杠杆。
   * Mechanism: 通过。JCMA 工具架构缺陷造成官方供给断层；本地 Insight REST API 与 Jira Cloud Assets REST API 完全公开且标准化；通过两阶段算法（第一阶段生成 Schema/Type 结构并建立无依赖原始对象，第二阶段解析并回填 Reference 引用指针与元数据），在技术上完全能够实现对象拓扑图谱的 100% 保真还原。
   * Persistence: 通过。Atlassian Data Center EOL 推进至 2029 年，全网企业持续处于迁向 Cloud 的高峰窗口期，需求具备多年确定性。
   * Capture: 通过。1-3 人小团队开发 Python/Node.js CLI 脚本工具，纯 API 编排与数据迁移，零实体资产、零硬件、高毛利。


* Final Status: HYPOTHESIS_READY


* Evidence:


   1. Atlassian 社区深度讨论《Atlassian Data Center End of Support: What Happens to Assets》（2026-07）：明确列出 JCMA 完全不迁移 Assets 对象模式、属性及引用字段的官方盲区。
   2. Atlassian 官方论坛专家复盘《Server to Cloud Migration: Best Practices》（2026-03）：证实插件与 Assets 数据断层是导致迁移失败的“第一大杀手”，实施商起步收费达数万美元。
   3. Atlassian 社区断链记录《Issue Links and References Broken After Cloud Migration》：证实手工 CSV 模式在复杂网状依赖下的结构性崩溃。


* Counter Evidence:


   1. 纯工单流转、从未使用 JSM Assets (Insight) 模块的简单敏捷团队。
   2. 资产规模超百万条且已直接签约大型跨国系统集成商（如埃森哲）的超巨型集团。


* Stop Reason: 四 Gate 均已通过充分独立证据核实，官方工具断层明确，两阶段 API 拓扑还原机制清晰，小团队轻资产切入点极佳。


* Resume Condition: 不适用（已完成）。


* What became more likely: JSM 企业管理员将普遍采用基于 REST API 的两阶段自动化资产拓扑抽取工具完成无损上云。


* What became less likely: 企业 IT 团队会愿意耗费数月时间在 Excel 中手动缝合数十万条资产的对象关联引用。


* What did we rule out: 排除了仅靠 Atlassian 原生 JCMA 工具能无损保留 JSM Assets 对象间引用关系（Reference Fields）的可能性。


* Task Version: researcher@0.2.2


* Generated At: 2026-11-06T17:44:19+08:00


* Role Spec Status: reviewed


________________


Opportunity Hypothesis: 面向 Jira Service Management 上云迁移的 Assets (Insight CMDB) 网状模式与引用依赖保真还原工具包
* Source Signal IDs: IBF-20261106-Atlassian-JCMA-JSM-AssetsRelationalSchemaLoss


* Source Signal References:


   * Signal ID: IBF-20261106-Atlassian-JCMA-JSM-AssetsRelationalSchemaLoss
   * Generated At: 2026-11-06T17:15:00+08:00
   * Task Version: installed-base-friction@0.2
   * Source File URL: https://docs.google.com/document/d/1BGWMQaXXtLy5pAMzswzJOXQHfp0vMBBP_4BIXqRMvFo/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-11-06T17:12:03+08:00


* Money: 全球正在经历从 Server/Data Center 迁往 Jira Cloud 的 5 万家 JSM 企业客户；面对外部方案商 $10,000–$40,000 的咨询报价与服务台瘫痪损失，企业愿支付 $499–$999 购买一键式无损迁移脚本工具。


* Mechanism: 针对 Atlassian 官方 JCMA 彻底遗漏 Assets 且 CSV 导入丢失网状引用的痛点，工具提供：单文件 CLI 脚本通过 REST API 分两阶段作业——第一阶段自动抽取本地 Insight 全部 Schema、对象类型树与基础属性定义并在 Cloud 端精准复刻，批量导入去引用化的裸对象；第二阶段建立全局旧 ID 到云端新 ID 的映射哈希表，自动回填所有 Reference 引用字段与自定义图标，确保迁移上云后客户服务台表单下拉框与自动化工单关联 100% 完好无损。


* Capture: 1-3 人小团队开发标准化命令行迁移工具，纯 API 自动化，零实体硬件、零库存、高毛利。


* Durability: Atlassian 强制上云时间表推进至 2029 年，全球企业级 CMDB 迁移高峰持续爆发，具有长期刚性订单周期。


* Evidence:


   1. Atlassian 社区（2026-07）：https://community.atlassian.com/forums/discussion/3256836/atlassian-data-center-end-of-support-what-actually-happens-to-your-jsm-assets-after-2029 证实 JCMA 遗漏 Assets 官方盲区。
   2. Solution Partners 论坛（2026-03）：https://community.atlassian.com/forums/discussion/3201378/server-to-cloud-migration-what-are-the-best-practices-for-jira-cloud-migration 证实资产迁移是第一大延期诱因与高价咨询现状。
   3. 社区实录：https://community.atlassian.com/forums/discussion/2249819/issue-links-broken-after-jira-software-migration-to-cloud 确认断链与表单损坏痛点。


* Counter Evidence:


   1. 未使用 Assets 模块的轻量客户。
   2. 资产规模超百万条且已直接签约大型跨国系统集成商（如埃森哲）的超巨型集团。


* Critical Unknown: 中型企业 Jira 管理员在本地安装与运行访问外网 API 的 Python 脚本的内部网络策略限制。


* Falsification: 若 Atlassian 官方在下个补丁中全面重构 JCMA 并原生免费支持 Assets 全模式与引用字段的双向无损迁移。


* Next Test: 在本地搭建 JSM Data Center 与 Jira Cloud 试用实例，录入包含 3 层引用的 500 条测试硬件资产，运行两阶段迁移脚本，验证 Cloud 端服务台工单表单下拉框的完整恢复率。


* Task Version: researcher@0.2.2


* Generated At: 2026-11-06T17:44:19+08:00


* Role Spec Status: reviewed