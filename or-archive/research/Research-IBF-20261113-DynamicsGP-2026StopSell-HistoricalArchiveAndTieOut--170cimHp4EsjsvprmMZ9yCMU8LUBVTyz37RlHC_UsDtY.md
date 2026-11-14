<!-- Source Google Doc: https://docs.google.com/document/d/170cimHp4EsjsvprmMZ9yCMU8LUBVTyz37RlHC_UsDtY/edit?usp=drivesdk
Drive ID: 170cimHp4EsjsvprmMZ9yCMU8LUBVTyz37RlHC_UsDtY
Modified: 2026-11-13T10:00:58.376Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: IBF-20261113-DynamicsGP-2026StopSell-HistoricalArchiveAndTieOut
* Source Signal References:
   * Signal ID: IBF-20261113-DynamicsGP-2026StopSell-HistoricalArchiveAndTieOut
   * Generated At: 2026-11-13T17:45:00+08:00
   * Task Version: installed-base-friction@0.2
   * Source File URL: IBF-20261113-DynamicsGP-2026StopSell-HistoricalArchiveAndTieOut.md
   * Source File Modified At: 2026-11-13T17:44:13+08:00
* Research Level: R2 — Economic Underwriting
* Stage Result: HYPOTHESIS_READY
* Final Status: HYPOTHESIS_READY
1. Unknown Ledger
Known
微软已于 2025 年 4 月 1 日停售 Dynamics GP 永久许可，并于 2026 年 4 月 1 日正式停售所有新订阅许可，官方产品与税务补丁支持将于 2029 年 12 月 31 日终止（安全补丁于 2031 年 4 月 30 日硬关停，底层 SQL Server 2016 已于 2026 年 7 月失去支持）。在 2026 年迁往 Dynamics 365 Business Central (BC) 的浪潮中，微软官方 Cloud Migration Tool 存在结构性缺口：仅导入汇总余额而不将历史总账（GL）明细迁入 BC 实时账簿，且完全不迁移企业长期依赖的 SmartLists 自定义报表；将 15–25 年历史强行塞入 BC 会触发存储与许可膨胀，未清理的子账漂移（AR/AP 控制科目与明细不平）更会导致迁移直接报错失败。当前商业历史数据归档与 SmartList 替代方案 eOne Popdock 订阅费高达 $150–$650/月（$1,800–$7,800/年，另加扩展模块各 $100/月及 Azure Data Lake 存储费），而 BC 标准实施项目报价达 $25,000–$80,000。若保留旧 Windows/SQL Server 虚拟机仅用于 IRS 3–7 年税务审计查账，则持续承担老旧系统安全合规风险。
Unknown
准备在 2026–2029 年从 Dynamics GP 迁往 BC/Sage Intacct/NetSuite 的中型企业中，未由原 VAR 合作伙伴强制捆绑采购 Popdock、而是愿意使用一次性买断的离线 DuckDB/HTML 便携归档包的比例。
Decision-Critical Unknown
正在撤离 Dynamics GP 的中型企业财务总监（Controller/CFO）或独立 ERP 迁移顾问，对于一款"只读 T-SQL + Python 打包器，一键抽取 GL20000/GL30000/PM/RM/POP 历史与 SmartList 定义，生成零月费加密 DuckDB + 静态 Web 检索档案及迁前子账漂移体检报告（单公司库 $299 买断，多公司/顾问包 $699）"的直接采购意愿。
2. Gate Checks
* Money: 通过。Popdock 最低档年费 $1,800 起（Business 档 $4,200/年），3–7 年税务保存周期累计支出 $5,400–$29,400；BC 实施费 $25,000–$80,000。$299 一次性买断工具对比首年订阅费即具备 6 倍杠杆，7 年周期超 18–90 倍。
* Mechanism: 通过。Dynamics GP 核心 SQL Server 表结构（GL20000/GL30000/PM30200/RM30101/POP30100）全行业高度统一；通过只读 T-SQL 一次性抽取并打包为本地 DuckDB + 静态 Web 查询包，同时执行控制科目与子账余额比对，既消除持续 SaaS 月费与老 SQL Server 安全风险，又前置拦截导致 BC 迁移失败的子账漂移。
* Persistence: 通过。2026 年 4 月刚进入订阅停售，停支与迁移窗口延续至 2029–2031 年，且税务审计归档需维持 7 年可查，需求具备多年确定性。
* Capture: 通过。1–3 人小团队开发纯只读 T-SQL + Python 打包脚本与静态 HTML 查询界面，不写入生产 ERP，零云端托管责任、零实体库存、高毛利。
3. Evidence & Counter Evidence
Supporting Evidence
1. ClonePartner GP 迁移实务（2026-05-04）：详述 2026-04-01 停售新订阅、2029/2031 停支时间线，以及官方 Cloud Migration Tool 不迁 GL 明细、不迁 SmartLists 及子账漂移阻断加载的局限。
2. Stoneridge Software Popdock 方案（2026-01-13）：微软合作伙伴证实全量历史迁入 BC 触发容量与性能问题，行业标准是剥离归档并通过外部工具查询。
3. eOne Solutions Popdock 官方定价：证实 Startup $150/月、Business $350/月、Premium $650/月，Scheduling/Matrix Reports 另各收 $100/月，支持工时 $250/小时。
4. Business-Software 2026 GP 迁移指南（2026-11-12）：确认截至 2026 年 11 月微软官方仍仅提供汇总余额与有限历史快照，需外部归档方案。
Counter Evidence
1. 高度依赖第三方 ISV（如 Mekorma 支票影像或自定义 Dexterity 扩展表）的企业，纯标准 GP 核心表抽取可能遗漏部分定制业务附件。
2. 部分中型企业完全依赖原 VAR 实施商打包采购，倾向于继续接受 VAR 推荐的 Popdock 订阅。
4. Decision Trail & Metadata
* Stop Reason: 四 Gate 均已通过充分独立证据核实，2026 年停售时间线、原生迁移工具断层及 Popdock 高额年费锚点明确。
* Resume Condition: 不适用（已完成）。
* What became more likely: 撤离 Dynamics GP 的财务团队与独立顾问将寻求零月费、自托管的便携 DuckDB/HTML 审计归档方案替代高价 SaaS。
* What became less likely: 企业在停用 GP 后愿意为了每年查几次历史发票而继续向 Popdock 支付 $1,800–$7,800/年或保留高危旧 SQL Server VM。
* What did we rule out: 排除了微软官方 Cloud Migration Tool 会将 15–25 年 GP 明细与 SmartLists 完整无损迁入 BC 实时账簿的假设。
* Task Version: researcher@0.2.2
* Generated At: 2026-11-13T17:57:15+08:00
* Role Spec Status: reviewed
Opportunity Hypothesis
Title: 面向 Dynamics GP 退市迁移的零月费便携审计归档与迁前子账体检套件
Source Signal References
* Signal ID: IBF-20261113-DynamicsGP-2026StopSell-HistoricalArchiveAndTieOut
* Generated At: 2026-11-13T17:45:00+08:00
* Task Version: installed-base-friction@0.2
* Source File URL: IBF-20261113-DynamicsGP-2026StopSell-HistoricalArchiveAndTieOut.md
* Source File Modified At: 2026-11-13T17:44:13+08:00
Money
北美数以万计仍运行本地 Dynamics GP 的中型制造、分销与医疗机构，面临 $1,800–$7,800/年 Popdock 订阅费与 $25,000–$80,000 BC 实施费。财务总监或独立迁移顾问愿支付 $299（单公司库买断）或 $699（多公司/顾问授权包）消除持续年费并前置排雷。
Mechanism
1. 标准核心表只读抽取：通过只读 T-SQL 脚本从 GP SQL Server 抽取 GL20000/GL30000/PM30200/RM30101/POP30100 等全量历史与 SmartList SQL 定义，不写入生产库。
2. 零月费便携 DuckDB + Web 检索包：打包为单文件加密 DuckDB + 本地零依赖静态 HTML 查询界面，财务人员关停老 SQL Server 后仍可毫秒级按科目、供应商、发票号检索并导出 Excel，满足 7 年 IRS 审计。
3. 迁前子账漂移体检报告：自动核对 AR/AP/Inventory 控制科目与子账明细余额，提前标出导致 Business Central Cloud Migration Tool 拒绝加载的不平差异行。
Capture
1–3 人小团队构建标准化 T-SQL + Python 打包工具，纯本地软件买断交付，零云端数据托管负担与实体库存。
Durability
GP 停售与停支窗口横跨 2026–2031 年，且 7 年法定审计保留期使离线归档需求具备长期确定性。
Evidence
1. ClonePartner (2026-05)：证实 2026 停售、原生工具不迁 GL 明细/SmartList 及子账漂移问题。
2. Stoneridge Software (2026-01)：证实剥离归档为行业标准方案。
3. eOne Popdock Pricing：证实 $150–$650/月高额订阅锚点。
Counter Evidence
1. 高度依赖第三方 ISV 自定义表的老旧 GP 环境。
2. 完全被 VAR 捆绑采购 Popdock 的大型客户。
Critical Unknown
撤离 Dynamics GP 的中型企业中，由独立财务总监或中小顾问主导选型（而非被原 VAR 强制捆绑 Popdock）的占比。
Falsification
若微软免费开放官方无限制、免 Popdock 订阅的 Azure Data Lake 历史 SmartList 内置查询器给所有 BC 迁移用户。
Next Test
在 GP 标准 TWO 测试库上运行只读 T-SQL + Python 打包脚本，验证 10 万行 GL 抽取打包至 DuckDB + 离线 HTML 界面及 AP 控制科目差额捕获能力，并在 r/DynamicsGP 邀请 2 位迁移顾问试用反馈。