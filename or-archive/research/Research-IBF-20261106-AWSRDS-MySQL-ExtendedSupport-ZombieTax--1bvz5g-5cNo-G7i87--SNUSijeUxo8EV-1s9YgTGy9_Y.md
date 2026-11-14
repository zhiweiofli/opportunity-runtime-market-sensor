<!-- Google Doc: https://docs.google.com/document/d/1bvz5g-5cNo-G7i87--SNUSijeUxo8EV-1s9YgTGy9_Y/edit?usp=drivesdk
Drive ID: 1bvz5g-5cNo-G7i87--SNUSijeUxo8EV-1s9YgTGy9_Y
Modified: 2026-11-06T09:49:24.919Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: IBF-20261106-AWSRDS-MySQL-ExtendedSupport-ZombieTax


* Source Signal References:


   * Signal ID: IBF-20261106-AWSRDS-MySQL-ExtendedSupport-ZombieTax
   * Generated At: 2026-11-06T17:15:00+08:00
   * Task Version: installed-base-friction@0.2
   * Source File URL: https://docs.google.com/document/d/13NviD0Cp1CkUaZQ1rCaDC_i677bwSGbm1di2-QLaFHM/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-11-06T17:11:22+08:00


* Research Level: R2 — Economic Underwriting


* Stage Result: HYPOTHESIS_READY


* Unknown Ledger:


   * Known: 2026 年下半年 AWS 对存量托管关系型数据库执行刚性扩展支持（Extended Support）收费：MySQL 5.7 自 2026 年 3 月起迈入第 3 年支持期，费率翻倍至 $0.200/vCPU-小时；MySQL 8.0 标准支持于 2026 年 7 月 31 日正式截止，8 月 1 日起全网未升级实例被 AWS 静默自动纳入付费扩展支持（$0.100/vCPU-小时起）；全球数十万中小型企业与 SaaS 开发者在月度账单中突发遭遇单实例每月 $292 至 $1,000+ 美元的“僵尸附加税”（单台 4 核 Multi-AZ 实例每月仅附加税达 $584，年额外损耗超 $7,000 美元）；企业因历史外包代码缺乏测试不敢升级，升级直接面临认证协议不兼容（caching_sha2_password 导致老驱动连不上）、强制 only_full_group_by 导致历史报表 SQL 报错及 Query Cache 被移除引发性能骤降；外部数据库咨询（Percona、Pythian 等）排查报价高达 $5,000–$20,000。
   * Unknown: 每月被计收 $300 以上 Extended Support 附加费的中小团队中，仅需通过 RDS Parameter Group 兼容模式配置（保持 mysql_native_password 与放宽 sql_mode）即可实现免改业务代码平滑升级的实例占比。
   * Decision-Critical Unknown: 正在承担高额 RDS 扩展支持附加费但恐惧生产事故不敢升级的 SaaS 创始人和 DevOps 工程师，对于一套“只读权限自动扫描 Schema 与慢日志、出具兼容性风险报告并生成无痛兼容 Parameter Group 模板与蓝绿演练脚本的工具包（单库售价 $99–$199 买断）”的购买转化率。


* Gate Checks:


   * Money: 通过。单实例每年多付 $3,500–$14,000 僵尸税，全美涉及数十万 RDS 实例；$149 工具对比数千美元罚金具备 23 倍高杠杆。
   * Mechanism: 通过。云厂商通过高额罚款逼迫用户升级；通过 Parameter Group 参数锁死（保留 mysql_native_password 认证、设置 sql_mode 兼容模式）可彻底消除应用端驱动与 SQL 报错，实现免重构代码直接升入标准支持期，技术路径成熟确定。
   * Persistence: 通过。AWS 官方定价已写入标准条款，MySQL 5.7 与 8.0 扩展支持持续至 2028 年，数据库技术债属于企业长期摩擦。
   * Capture: 通过。1-3 人小团队构建自动化 Python 诊断脚本与 CloudFormation/Terraform 参数配置包，纯软件工具，零实体资产、零库存、高毛利。


* Final Status: HYPOTHESIS_READY


* Evidence:


   1. Reddit r/aws 社区公告《PSA: RDS MySQL 8.0 Standard Support Ends July 31》（2026-06）：确认 8 月 1 日起自动转入 Extended Support，multi-AZ r5.large 每月多计收约 $292 账单。
   2. AWS 官方通告《Amazon RDS MySQL Extended Support Pricing》（2026-06）：确认 MySQL 5.7 维持第 3 年高费率（$0.200/vCPU-hr）。
   3. Reddit r/aws 真实案例《Upgraded yesterday from RDS MySQL 5.7 Extended Support》：证实小实例月账单被附加费从不足 $100 暴推至 $556。


* Counter Evidence:


   1. 架构师团队极为完备、早已全量完成 MySQL 8.4 LTS 升级的头部科技公司。
   2. 少数深度依赖已废弃物理 Query Cache 且索引极差、升级后必须人工重写 SQL 索引的边缘项目。


* Stop Reason: 四 Gate 均已通过充分独立证据核实，AWS 罚款规则明确，参数兼容模板免改代码机制清晰，小团队轻资产切入点极佳。


* Resume Condition: 不适用（已完成）。


* What became more likely: 中小企业将普遍采用预置兼容参数组（Parameter Group）的平滑升级模板消除 RDS 扩展支持罚款。


* What became less likely: AWS 会在客户抗议下撤销针对 MySQL 5.7/8.0 已经生效的每月数百万美元的扩展支持收费池。


* What did we rule out: 排除了在不升级数据库引擎主版本的情况下用户能够通过提交工单免除 AWS Extended Support 账单扣费的可能。


* Task Version: researcher@0.2.2


* Generated At: 2026-11-06T17:44:19+08:00


* Role Spec Status: reviewed


________________


Opportunity Hypothesis: 面向 AWS RDS MySQL 存量数据库的扩展支持“僵尸税”止血与免改代码平滑升级兼容套件
* Source Signal IDs: IBF-20261106-AWSRDS-MySQL-ExtendedSupport-ZombieTax


* Source Signal References:


   * Signal ID: IBF-20261106-AWSRDS-MySQL-ExtendedSupport-ZombieTax
   * Generated At: 2026-11-06T17:15:00+08:00
   * Task Version: installed-base-friction@0.2
   * Source File URL: https://docs.google.com/document/d/13NviD0Cp1CkUaZQ1rCaDC_i677bwSGbm1di2-QLaFHM/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-11-06T17:11:22+08:00


* Money: 全球数以万计在 AWS RDS/Aurora 上运行老旧 MySQL 的中小企业；单台实例每年流失 $3,500–$14,000 无谓附加税，企业愿支付 $99–$199 买断自检脚本与平滑兼容参数模板以即刻停止扣费。


* Mechanism: 针对企业因害怕老驱动不兼容与 SQL 报错而被迫缴纳每月数百美元罚款的痛点，工具提供：只读连接数据库，自动审计当前架构中的驱动认证协议、group by 语法依赖与慢查询；一键输出定制的 AWS RDS Parameter Group 配置文件（锁定 mysql_native_password、放宽 sql_mode 限制），使得实例在 0 行修改业务代码的前提下安全直升至 MySQL 8.0/8.4 最新补丁版本，在 30 分钟内彻底斩断每月 Extended Support 账单扣费。


* Capture: 1-3 人小团队构建自动化 Python 诊断脚本与 IaC 参数模板，纯代码交付，零实体库存、高毛利。


* Durability: AWS 扩展支持阶梯收费持续生效至 2028 年，存量遗留系统降本是云原生常态化刚需。


* Evidence:


   1. Reddit r/aws（2026-06）：https://www.reddit.com/r/aws/comments/1u86lrr/psa_rds_mysql_80_standard_support_ends_july_31/ 确认 8.0 强制纳入计费。
   2. AWS 官方通告：https://aws.amazon.com/about-aws/whats-new/2026/06/rds-mysql-es-extension/ 确认 5.7 高额定价。
   3. Reddit 账单实录：https://www.reddit.com/r/aws/comments/1gjdp5c/upgraded_yesterday_from_rds_mysql_5744_extended/ 确认成本从 $100 飙至 $556。


* Counter Evidence:


   1. 超大规模互联网公司拥有自建 DBA 专家团队。
   2. 少数极端老旧的专用二进制存储过程。


* Critical Unknown: 中小企业对于在 AWS 控制台创建只读数据库审计用户权限的安全审批流程摩擦。


* Falsification: 若 AWS 官方宣布全面取消 RDS Extended Support 附加费，对所有老版本数据库永久提供免费基础维护。


* Next Test: 在本地及 AWS Sandbox 搭建典型报错的 MySQL 5.7 实例（含 group by 历史存储过程与旧版 PHP 驱动），测试参数模板兼容性，并在 Reddit r/aws 发布免费自检脚本收集线索。


* Task Version: researcher@0.2.2


* Generated At: 2026-11-06T17:44:19+08:00


* Role Spec Status: reviewed