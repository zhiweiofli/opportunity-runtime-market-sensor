---
requirement_id: market-v1
revision: 2
supersedes: market-history-v1-revision-1
authority: user-correction-and-us-priority
status: ready-for-development
target_task_version: 0.3.0
platform: github-actions-python-tushare
role_spec: docs/03-market-sensor.md
updated_at: 2026-10-20
---

# Market Sensor V1：美股资金配置变化 → Researcher R1

## 1. 定位、纠偏与成功标准

用户明确要求“错了就改”，并确认优先覆盖美股。原 docs/00-overview.md 的问题是：哪里的资金流或结构变化可能造成可重复的错误定价？Market 原稿要求可量化、有历史背景、有潜在经济机制、有可交易工具且流动性不明显不足的异常，再交 Researcher。

revision 1 先选6只A股和量价阈值，未由经济问题推导对象；全部候选 research_eligible=false 后又要求人先补机制，偏离原角色链路。重叠5日收益的多次命中也不能排除同一次跳动。本 revision 取代旧业务目标，旧版本在 Git 历史保留，不改写六份原稿。

**第一版回答：美国国内股票基金类别的净新配置，是否由持续流入转为持续流出，或反向变化，且规模足以值得调查边际需求与相对定价？** 它是 Flow Shift 的早期线索，不是“市场即将上涨/下跌”或已证明错价。

成功标准：能交出少量原始证据可追溯、钱的规模明确、潜在机制具体、可被证伪的真实 Signal，让 Researcher 的 R1 回答 Money/Mechanism；不只是运行算法、画图或定时生成报告。合法无信号是正常结果。R1 可以 KILL，不以发现机会数量为KPI；2–3个策略是完整研究/验证链路的阶段目标，不是Sensor承诺。

固定执行仍为 GitHub Actions + Python，保留 Tushare Pro 入口。Tushare股票成交额不能替代基金申赎/ETF净发行，因此为美国资金配置问题补充 ICI 原始公开发布，必要的工具身份/流动性使用发行人原始披露。这是有业务依据的数据补充，不迁移平台、不增角色/后端。美股Tushare独立权限、ETF/等权指数覆盖均未验证，不承诺已有权限，不购买或复制凭据，不为迁就数据源退回A股。

目标0.3.0仍是未发布的PR版本；旧PR中0.3.0代码未合并，不因需求纠偏虚增0.3.1。当前默认分支部署仍0.2.0。

## 2. 收藏页怎样使用

[用户收藏的 Big Picture](https://laoqianritan-create-github-io.pages.dev/#panel-eps)用于提出问题和识别来源，不是生产Signal唯一数据源。其有价值的视角是盈利/估值、资金配置、市场集中度及风险的关系，不复制其仪表盘、全套面板或阈值。

- 首条可执行规则从ICI基金申赎与ETF净发行开始，不以股票价格变化猜钱流。
- EPS先作解释背景：实际/名义、TTM/forward、reported/operating、通胀基期、报告期/发布日必须统一；插值月不是新盈利发布，历史重述不是当时已知信息。暂不在生产规则中抓EPS或用“名义价格/实际EPS”算P/E。
- 市值/等权表现、盈利与估值的分解，以及VIX/实现波动率，是后续可评估的证据关系；数据口径与机制确认前不列本轮必做、不假定价差必然收敛。

具体已查证内容和限制见 [页面评估](market-page-assessment.md)、[美股机制与数据边界](market-etf-mechanism-references.md)。原A股数据笔记只保留历史参考。

## 3. 第一个机制规则

规则ID：`us_domestic_fund_flow_reversal_v1`。Type=Market，Signal Class=Flow Shift。对象是ICI合并周报Domestic equity类别的行业估计，不是单只ETF、全部美国股市成交资金或某批投资者身份。

Money证据：共同基金净新现金流估计与ETF净发行估计的合并类别数值。申购/赎回或份额发行变化会改变基金体系的配置压力，但现金缓冲、实物申赎、其他持有人交易及预先定价可能削弱对底层价格的影响。这是有来源和对象的潜在机制，**不是**已经证实的底层买卖、价格因果或套利收益。

首版采用下列可修改的试运行物质性/持续性标准，不宣称历史校准或预测有效：

| 项目 | 本轮规则 |
| --- | --- |
| 核心来源 | https://www.ici.org/research/stats/combined_flows ，合并报告，不混用仅mutual fund或仅ETF的表 |
| 核心类别 | Domestic equity；其他类别只作原始上下文，World不简称“非美”，也不证明同一笔钱从A迁到B |
| 可用历史 | 同一次已取得发布中的最近4个不同报告周，按week_end排序；公开页本次可见5周，**不依赖尚未证实可得的104/156周会员历史** |
| 前后区间 | 前2周 vs 后2周，4个不重叠周；周末间隔正常应5–9自然日，缺周/重复/含义不明则BLOCKED，不插值或补零 |
| 流出反转 | 前2周各自>0，后2周各自<0；两个区间各自的净额绝对值均>=5,000百万美元 |
| 流入反转 | 前2周各自<0，后2周各自>0；两个区间各自的净额绝对值均>=5,000百万美元 |
| 其他情况 | 不生成该规则Signal；零值不算正/负，不把持续同向流动或单周反向当本规则新反转 |
| Magnitude | 两区间有符号净额、其差额（后-前）、原4周数值、单位USD million及完整周日期，不伪造历史分位 |
| Persistence | “持续”仅指两个不同报告周同方向，披露估计/修订；不推断结构永久持续 |
| 时间新鲜度 | 发布日<=as_of，发布日至as_of不超过14自然日；最新报告周距发布日<=14自然日。异常延迟则BLOCKED，不猜例行发布时间 |
| 输出上限 | 首版此规则每个发布/数据版本最多1条，不强求每轮有Signal |

5,000百万美元是本轮用于避免微小净额噪声的工程物质性门槛；2周是不同统计区间的持续观察要求。均不是收益阈值，不宣称经过历史优化；修改需spec/config/version/CHANGELOG追溯。

首版潜在可交易观测载体使用美国广泛股票市场ETF（先核对SPY）。它只证明相关市场存在可交易工具，不等于ICI类别的精确复制或已选定表达交易。发行人公开资料须确认上市/币种，且同一数据日期的价格与成交股数可核对、日期不晚于as_of且距as_of<=14自然日，单日美元成交额代理price×shares至少1亿美元；这是“流动性不明显不足”的粗筛，不是滑点/容量/成本验收。不能把过旧报价、NAV或基金总资产当成交额。

优先预检Tushare us_daily是否具备权限、SPY覆盖及成交量单位；文档或实测不支持时使用State Street原始产品数据的公开价格/Exchange Volume字段，保留源、日期与单位。发行人页面入口：https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-500-etf-trust-spy 。没有已核验的身份/流动性数据则只保存Flow观察并报告BLOCKED，不伪造/换成A股，也不启动买卖。

## 4. 数据预检、来源与point-in-time

先实现并实际执行源预检，再接生产规则：

1. 从ICI原始公开HTML读取当前标题、发布日期、分类、单位及周表；保存原始响应快照（artifact，不复制整页到Git）、URL、retrieved_at、SHA-256及规范化行。不能把登录页、403、空表或收藏站JSON当ICI成功取数。
2. 验证为combined类别和USD million；数字逗号、负号、空缺与零分开，NaN/Inf/重复冲突为错误。分类/单位改变则BLOCKED，不模糊猜“相似表”。因四舍五入，不用逐项绝对相等校验强行否定原始类别值。
3. 文档来源解释归属和机制，公开发布是数值源；二者同提供者不能冒充独立证据。历史XLS若403/会员限制，正常报告，不绕过、不请求用户为此购买、不以该不可用长历史阻塞四周规则实现。
4. 保留period_end、published_date、retrieved_at、vintage/hash。ICI旧周会修订，按本次已知数据评价；不能叫实时、初值、月度实际或全市场净流量。
5. as_of可传ISO时间（带时区）或日期。来源只有发布日期时保留date精度，保守以该日America/New_York结束后才可使用；不能补造精确发布时间或用报告期末代替发布日。默认as_of为本次实际时间。
6. 历史重放只能使用as_of之前已经保存的发布快照/合法提供的带可得时间资料；仅有今天重述的历史或没有vintage时返回BLOCKED，不把固定滞后天数当历史发布记录。fixture可以测试所有分支但始终synthetic。
7. 来源快照/下载权限失败，只阻塞有关规则；保留已有模块和失败事实，不换成股票成交额或网页截图估算。缺数据不能写NO_SIGNAL，只有有效完整评估且无触发才可NO_SIGNAL。

不新增数据库或采集服务。文件、Git配置及已有Actions artifact足够；美股权限/额外数据本轮有明确预检状态，不要求把GitHub的TUSHARE_TOKEN交给Cloud。云端可开发/测试公开源；真实Tushare预检只在Actions runner使用现有Secret，源明确隔离，token不发到ICI/发行人主机或日志。

本机2026-10-20直接HTTP预检：ICI combined返回403，发行人响应读取不完整；检索工具可读内容不等于Python/Actions自动接入通过。云端必须先核验其实际网络；只使用公开链接的正常HTML/打印发布格式，不绕过登录/会员/访问限制，不为抓取新增浏览器服务。若云端同样受阻，生产live模式返回BLOCKED并保存报告；支持`supplied_snapshot`（用户合法保存的原始发布/产品数据+来源URL/实际取得时间）作为输入回退，与`live_http`、`synthetic_fixture`明确区分。缺来源/时间或无法解析验证的快照不能放行；实际人工输入不登记为自动抓取成功。人工只提供原始资料，不代做机制研究。

## 5. Signal → Researcher 的实际交接

真实源数据、反转/物质性/持续性、时间质量、具体机制说明和工具/流动性检查全部满足时，生成 `research_eligible=true` 的Market Signal供R1；不再一概false或要求人先完成机制研究。fixture始终demo_only=true、research_eligible=false。真实源规则仍 `rule.status=trial`、demo_only=false；true只表示可进入R1，不代表通过Money/Mechanism/Persistence/Capture四Gate、策略有效或可以买卖。

Signal保留公共字段及原稿Anomaly/Instrument/Magnitude/Persistence/Possible Mechanism/Data Quality。Evidence 2–4条定位到原始数值快照/URL与日期、ICI分类和发行人/已核对行情事实；明确来源依赖，不伪造独立性。Money保留估计金额，不称收入/利润。可能机制与事实分栏。

Next Question交Researcher R1：这次申赎/发行方向变化是否形成可重复的底层需求压力，还是载体迁移、现金管理、季节性或修订？市场是否已反映？哪些证据能KILL该机制？表达成本/工具匹配未知交由后续研究，不要求人预先答完。已知有强反证（类别错配、工具不可用等）则不放行。

输出JSON、中文report.md及可直接交接的researcher-packet.md；packet内嵌可读原4周事实、具体机制、反证/未知、原始URL/日期/哈希、版本与观察标识，不能只给本机路径。合格packet由人保存到Drive Signals/Market即可，不要求其先补一份研究；不新增自动Drive服务。R1合法KILL并保留理由。

运行状态分清SIGNALS、NO_SIGNAL、BLOCKED（数据/权限/质量不足）、ERROR（参数/程序/写出错误）；旧demo命令原有状态兼容。观察背景和未过门槛项进observations/coverage，不混入合格signals[]，不给所有行套通用机制强行放行。

身份与重复：稳定Signal ID由规则ID、最新报告周及方向组成；另存observation_id/数据指纹（规范化4周数值、发布日、规则配置/版本）。同一发布相同指纹重复运行不是新证据。若有上次报告，以代码复用匹配Signal原Generated At/内容，报告运行时间独立更新；修订改变指纹则新观察并明确修订。可用原生artifact取上次报告（必要时增加actions:read，只读），不建状态服务。未取到历史则标dedup未核实，人工按稳定ID/指纹避免重复保存，不声称全局新Signal。保留Researcher现有观察键协议，不偷偷改变其他角色Prompt。

## 6. 模块、调度与旧代码处理

复用已完成的HTTP/校验/重试、报告、artifact和手动入口，只补最小US流向解析/规则/packet与来源预检，不做通用插件/指标框架。当前PR #2及分支保留，不重建仓库、不丢弃已完成工作。

原6股price_volume_stress规则退出生产默认和完整Market验收，只可作为明确标注的legacy/demo实验入口，research_eligible=false；重叠收益2/3命中不再声称“排除了单点跳动”。旧兼容测试可保留为回归，不算新业务验收。移除默认/定时中的6股配置；无须为了新规格删除所有可复用历史工具。

新定时是**每周五08:17 Asia/Taipei**（试运行默认，对应周度发布节奏，非原已定周期）；不再沿用A股工作日晚间。cron `17 8 * * 5` + timezone:Asia/Taipei；若实际平台明确拒绝timezone字段，等价UTC `17 0 * * 5`，保留拒绝/回退证据。不承诺固定发布时刻；14日新鲜度按实际发布检查。保留手动运行/快照重放；schedule按event明确用US flow配置，不拿空inputs/fixture当真数据。

CI离线；dispatch可用于公开源预检/真实报告。每轮覆盖当前快照并保存JSON/Markdown/packet及必要原始来源，artifact按run_id/attempt唯一保留14天。相关错误/阻塞也须保存，写出失败非零；不自动提交行情数据到Git。权限维持只读，若为跨run artifact去重增加actions:read须在PR解释用途；不增加写仓库、Drive或长期凭据权限。

发布到默认分支前不启用新定时，不自动合并PR。task/code/workflow版本统一0.3.0，CHANGELOG重写围绕最终US流向行为，保留旧原型为已弃用的历史；原稿/PROJECT_GUIDE字节不变，其他角色/公共协议不虚增版本。

## 7. 验收与完成标准

| 用例 | 测试与通过标准 |
| --- | --- |
| US-01 定位 | 需求/README/任务/默认配置均为美股Flow Shift；无默认6股扫描、泛化“涨跌=机会”或要求人先补机制 |
| US-02 正反例 | 4个不重叠周，前两周各+3000后两周各-4000（单位百万）→流出反转；对称流入→反向；只有单周翻转、持续同向、区间净额不足、零值→无信号 |
| US-03 金额边界 | 两区间各绝对值恰5000通过；略低不通过；百万/美元/千元不能混，符号、逗号、小数/缺值正确；不虚构历史分位 |
| US-04 真实解析 | 保存实际公开ICI HTML，核对combined、Domestic分类、单位、4周、发布日、raw hash；登录页/403/单位类别漂移→BLOCKED；真实无反转应NO_SIGNAL，不为验收造命中 |
| US-05 数据与时间 | 重复周/缺周/错序/未来发布/过旧发布、unknown发布日、日期精度/NY夏令时分别覆盖；按发布可得时间拒绝未来数据，不以期末或插值填充 |
| US-06 修订与重放 | 当前修订值不回填历史PIT；相同指纹复用Generated At；新修订新观察；仅当前网页无法重放过去则BLOCKED；原始快照不丢 |
| US-07 工具与流动性 | 官方身份/日期/价格/成交股数可追溯、计算代理>=1亿美元；NAV/AUM当成交额、陈旧/错币种/错日期、Tushare无权限或ETF无覆盖不冒充通过；不足只保留观察 |
| US-08 研究交接 | 满足源/规则/机制/工具门槛时真实signal eligible=true，packet可独立读并交R1；fixture永远false；缺门槛不放行、不要求人先研究；无交易建议/Hypothesis |
| US-09 回归与故障 | 旧demo测试仍通过；网络/格式失败不回退数据，不上传旧成功报告、不泄露Secret；三份产物写出/失败artifact符合约定 |
| US-10 Actions | 静态/离线分别核对schedule与dispatch参数、台北周频、只读权限、artifact；实际dispatch保存run/产物；自然schedule须合并后独立回执，不拿手动代签 |
| US-11 业务案例 | 至少1个明确标为synthetic的完整正例（满足机制与工具证据夹具）走到R1 packet；至少1个公开真实发布案例，无命中可合格。证明的是线索可用性，不是盈利 |

先做数据可用性预检及以上离线实现/测试，再做公开源Actions实跑；Tushare美股权限不足不阻塞公开ICI部分，但工具证据不足不得签合格Signal。只有当前有的数据可用性是已验证，其他项如实列待验；不假造会员长历史、独立来源或交易成本结论。后续若要引入EPS/相对价值/波动率，另写机制与数据契约，不一口气建设全站。

交付更新同一PR #2，标题/说明重写成最终美股Flow Shift范围，附真实测试、原始来源、数据预检结果、公开源run、可复制命令、R1 packet样例及合并后定时待验。底座技术测试通过不等于业务定位通过。执行验证结果分层记录；不自动合并/交易。

## 实现输入与时间约定

生产入口为 `--mode flow`（无demo参数时默认），`--input-mode live_http|supplied_snapshot|synthetic_fixture`。快照 manifest 版本1，声明 synthetic，并逐源记录 file、source_url、retrieved_at（带时区）、原始字节sha256；原始HTML不改写，路径相对manifest。合法提供的原始资料才可标synthetic=false，示例夹具不能仅改模式就变成真实输入。缺元数据、哈希不符或不支持的HTML结构为BLOCKED。快照并非对来源真实性的密码学认证，提供者需如实声明来源；解析器不接受任意规范化数值JSON代替原始页。

`--as-of` 的日期格式YYYY-MM-DD解释为截至该纽约日结束（次日纽约00:00）；带时区ISO时间保留真实时点。发布日期仅为date时，available_after为次日纽约00:00，NY夏令时由zoneinfo计算；同时要求原始快照retrieved_at<=as_of，防止今天的修订值冒充早期vintage。默认as_of在本次源采集完成后取实际时间。新鲜度按纽约日期计算，日终日期不计入次日。工具价格与Exchange Volume继承同一Fund Market Price区块明确的as-of日期，单位必须明确为USD和Shares；不是NAV、AUM或全市场成交量。

规范化金额以十进制字符串保存，单位独立列出；指纹对4周数值、发布日、规则配置/版本做稳定序列化，不使用抓取时间充当新观察。`--previous-report` 可提供上次JSON，或在同一路径重跑时自动读旧报告；完全相同的Signal ID/指纹复用原Signal（包括Generated At），同ID新指纹标修订。没有上次资料则明确dedup未核实。原始源按内容哈希保留，报告和packet定位URL/时间/哈希；若跨run手动提供前次报告，应同时保留其原始来源artifact。V1不自动下载跨run artifact，也不新增actions权限，不声称全局去重。

旧 `--mode history` 使用 `config/legacy-market-history.json`，始终为legacy/demo且research_eligible=false；原有显式`--demo-abs-pct`命令保持兼容。重叠5日收益仅是旧原型回归，不证明多个独立冲击。生产配置与定时中不再包含6股名单。
