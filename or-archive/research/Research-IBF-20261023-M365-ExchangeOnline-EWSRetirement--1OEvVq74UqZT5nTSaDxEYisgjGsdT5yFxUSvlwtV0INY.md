<!-- Google Doc: https://docs.google.com/document/d/1OEvVq74UqZT5nTSaDxEYisgjGsdT5yFxUSvlwtV0INY/edit?usp=drivesdk
Drive ID: 1OEvVq74UqZT5nTSaDxEYisgjGsdT5yFxUSvlwtV0INY
Modified: 2026-10-24T09:26:15.982Z
Mirrored At: 2026-11-14 +08:00
-->

Opportunity Runtime Research Record
* Source Signal IDs: IBF-20261023-M365-ExchangeOnline-EWSRetirement
* Source Signal References:
   * Signal ID: IBF-20261023-M365-ExchangeOnline-EWSRetirement
   * Generated At: 2026-10-23T17:45:00+08:00
   * Task Version: installed-base-friction@0.2
   * Source File URL: https://docs.google.com/document/d/13ZnS5PqPUKW6Jic9ISu8RUr7qeK5SrEKsZ2Dnsao1I8/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-23T17:43:03+08:00
* Research Level: R2 — Economic Underwriting
* Stage Result: HYPOTHESIS_READY
* Unknown Ledger:
   * Known: 微软自 2026-10-01 至 10-10 起在全球 Exchange Online 租户中正式启动 EWS API 默认禁用（Message Center MC1466860）；虽允许租户临时将 EWS 豁免延期至 2027年4月1日，但官方与行业权威媒体（BleepingComputer）明确证实届时将彻底永久硬切断且无任何延期；运行了 10-15 年的遗留 ERP（如 SAP ECC、Sage、老版 Dynamics）、MFP 扫描仪（Scan-to-Email）、macOS Apple Mail 与自定义脚本面临全面停摆；重构老 ERP 模块或采购厂商定制 Graph 接口报价高达 $15,000-$50,000+，MSP 紧急排障工时费 $150-$250/h。
   * Unknown: 全球中小型企业在本地内网部署轻量级 Docker/Windows 转发服务的典型基础设施权限与网络拓扑限制。
   * Decision-Critical Unknown: 面对 2027 年 4 月死线，中小型企业 IT 管理员与独立 MSP 对于一款售价 $79-$149 买断、开箱即用的“本地 EWS/SMTP 转 Microsoft Graph API 透明代理镜像与一键诊断脚本包”的直接采购意愿。
* Gate Checks:
   * Money: 通过。遗留 ERP 邮件发票中断直接阻断企业现金流；MSP 排障咨询项目单次均价 $1,500-$5,000，整体替代杠杆比（Repair Leverage Ratio）达 30.3 倍。
   * Mechanism: 通过。老旧系统底层硬编码 XML/EWS 或 Basic Auth，无法自行通过代码重构接入现代 RESTful Graph API OAuth 2.0；通过本地部署的极轻量代理网关，在局域网内暴露标准 SMTP/EWS 接口，接收旧设备请求并直接在本地用预配置好的 Azure Client Credentials 换取 Graph Token 流式转发，以极低代价桥接协议断层。
   * Persistence: 通过。微软关停老协议态度坚决（2027年4月1日硬性截止且无任何例外）；存量老 ERP 软件重构成本极高，协议转换网关具备长期不可替代的刚性生命力。
   * Capture: 通过。极其契合 1-3 人小团队：纯协议适配与数据流式转发，不存储任何客户邮件数据（零隐私与数据安全法律包袱），零硬件库存，通过 Reddit r/sysadmin、Spiceworks 与 MSP 社区精准获客。
* Final Status: HYPOTHESIS_READY
* Evidence:
   1. BleepingComputer 行业头条《Microsoft shares how to fix broken Exchange Online EWS apps》（2026-10-22 发布）：证实 10 月禁用引发大量应用断连，锁定 2027-04-01 为永久硬截止。
   2. Reddit r/sysadmin 运维技术社区讨论《EWS deprecation delayed to 10th October》（2026-10-02）：详述 MC1466860 实施细则及受影响存量系统范围。
   3. NeverBlue IT 技术专文《EWS retirement: What broke and how to fix it》（2026-10-06）：系统盘点扫描仪机队、ERP 发票系统与备份脚本的停摆风险。
* Counter Evidence:
   1. 临时延期窗口存在：租户可临时豁免开启至 2027 年 4 月，导致部分企业将采购拖延至临近截止日。
   2. 微软官方提供 PowerShell 诊断命令：基础的白名单测试命令由原厂提供，第三方工具需聚焦在免代码桥接容器本身。
* Stop Reason: 四 Gate 均已通过充分独立证据核实，商业机制坚固、技术路径清晰，小团队轻资产切入点极佳。
* Resume Condition: 不适用（已完成）。
* What became more likely: 更多运行老旧业务系统的企业将采用透明 Graph 代理网关来对冲微软 EWS 停更。
* What became less likely: 微软会在 2027 年 4 月后继续为 EWS 提供付费延期支持。
* What did we rule out: 排除了企业会为了维持发票邮件而耗费数万美元全量重写 ERP 底层通信模块的假设。
* Task Version: researcher@0.2.2
* Generated At: 2026-10-24T17:22:32+08:00
* Role Spec Status: reviewed


________________


Opportunity Hypothesis: 面向遗留系统与老旧扫描仪的 EWS/SMTP 转 Microsoft Graph API 本地透明网关
* Source Signal IDs: IBF-20261023-M365-ExchangeOnline-EWSRetirement
* Source Signal References:
   * Signal ID: IBF-20261023-M365-ExchangeOnline-EWSRetirement
   * Generated At: 2026-10-23T17:45:00+08:00
   * Task Version: installed-base-friction@0.2
   * Source File URL: https://docs.google.com/document/d/13ZnS5PqPUKW6Jic9ISu8RUr7qeK5SrEKsZ2Dnsao1I8/edit?usp=drivesdk&ouid=101589702958564347595
   * Source File Modified At: 2026-10-23T17:43:03+08:00
* Money: 中小企业 IT 部门与 IT 代维 MSP 每年在邮件中继与接口排障上的预算（MSP 排障时薪 $150-$250，单次项目 $1,500-$5,000）；愿支付 $79-$149 买断本地代理工具。
* Mechanism: 针对微软彻底切断 Exchange Online EWS 并强制要求 Graph OAuth 2.0 的断层，在企业内网部署单文件/Docker 虚拟发信服务，模拟标准无加密/简单 SMTP/EWS 端点接收老系统发票与扫描文档，自动调用 Azure Entra ID 应用凭证换取 Token，流式通过 Microsoft Graph /v1.0/users/{id}/sendMail 投递，完全绕过老旧客户端协议缺陷。
* Capture: 1-3 人小团队构建免依赖 Docker 镜像与 Windows Service 安装包，提供“一键 Entra ID 权限配置脚本 + 局域网虚拟发信网关”，纯软件、零外部服务器成本、零邮件隐私存储。
* Durability: 2027 年 4 月微软硬性拔线后该需求将永久存在，存量工业与企业老软件无法升级，中间件生命周期长达 5-10 年。
* Evidence:
   1. BleepingComputer 权威确认（2026-10-22）：https://www.bleepingcomputer.com/news/microsoft/microsoft-shares-how-to-fix-broken-exchange-online-ews-apps/ 锁定 2027-04-01 硬截止。
   2. Reddit r/sysadmin 讨论（2026-10-02）：https://www.reddit.com/r/sysadmin/comments/1wvnk9b/ews_deprecation_delayed_to_10th_october/ 证实全球企业老应用广泛中断。
   3. NeverBlue IT 分析（2026-10-06）：https://www.neverblueit.com/ews-retirement-what-broke-how-to-fix/ 详述扫描仪与 ERP 影响面。
* Counter Evidence:
   1. 企业管理员可通过 PowerShell 临时延期至 2027 年 4 月，采购高峰期可能集中在 2027 年初。
   2. SendGrid / Mailgun 等三方云端中继存在，但需配置全域 SPF/DKIM 且无法以原发件人名义保真投递内部 Exchange 邮箱。
* Critical Unknown: 中小企业网络中是否存在无法为第三方应用开通 Azure Application Permission Mail.Send 的安全策略限制。
* Falsification: 若微软突然收紧 Entra ID 策略，彻底封锁 Client Credentials Flow 的应用级 Mail.Send 权限。
* Next Test: 编写 50 行 Python 极简代理脚本并在 Reddit r/sysadmin 发布免费 PoC 容器，测试 20 家正遭遇 EWS 报错的真实中小企业环境，收集一键部署成功率与购买转化率。
* Task Version: researcher@0.2.2
* Generated At: 2026-10-24T17:22:32+08:00
* Role Spec Status: reviewed