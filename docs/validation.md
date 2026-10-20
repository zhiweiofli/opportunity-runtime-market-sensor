# Market Sensor 验证记录

当前开发范围为末节0.3.0 revision 2美股Flow Shift；下列0.2.0及六股原型记录仅保留各阶段历史事实。

业务版本：0.2.0。部署不代表正式异常规则或交易策略已验收。历史 GitHub 实跑基于部署提交 `cfc65c27fa084cd232dd037d4717687dc7f17aa3`；本次云端验证基线和结果见下文。

| 阶段 | 状态与证据 |
| --- | --- |
| 私有 GitHub 仓库/推送 | 已创建并推送 [zhiweiofli/opportunity-runtime-market-sensor](https://github.com/zhiweiofli/opportunity-runtime-market-sensor)，main 分支 |
| 本地离线测试/CLI | Python 3.9.6，8/8 通过；fixture 3 observations→2 演示 Signal；YAML、导航、原始需求 SHA-256 核对通过 |
| Actions CI | [39350160142](https://github.com/zhiweiofli/opportunity-runtime-market-sensor/actions/runs/39350160142) 成功，Python 3.11 的 8 项测试与 CLI 报告断言 |
| Actions 手动 fixture | [39350184015](https://github.com/zhiweiofli/opportunity-runtime-market-sensor/actions/runs/39350184015) 成功，下载 artifact 核对 3 observations / 2 signals，版本 0.2.0、demo_only=true、research_eligible=false |
| 真实 HTTPS 首次尝试 | [39350190556](https://github.com/zhiweiofli/opportunity-runtime-market-sensor/actions/runs/39350190556) 缺 TUSHARE_TOKEN，ERROR / 0 Signal；错误报告正常保存，无合成数据回退 |
| Secret 修正/真实 HTTPS 重跑 | 用户在本仓库配置 Secret 后，[39350480874](https://github.com/zhiweiofli/opportunity-runtime-market-sensor/actions/runs/39350480874) 成功；下载核对 20261016 / 000001.SZ、1 条 observation、NO_MATCH / 0 Signal，source=tushare；demo_only=true、research_eligible=false |
| 正式规则/定时行情 | 用户将提供规则，具体市场/标的范围、历史基准、阈值、频率未收到；没有 schedule，不签正式异常识别/交易策略通过 |
| Codex Cloud | 历史 CLI 指定交接环境提交失败，未创建任务；2026-10-20 已在本聊天实际挂载的同仓库云端环境完成离线验收（8/8、fixture 与报告断言通过），详见下文；不代表历史 Environment ID 已可用或另一次 CLI 提交成功 |

真实 API 输入为 source=tushare、trade_date=20261016、ts_code=000001.SZ、demo_abs_pct=5，只是接线样例，不是标的/规则决策。重跑报告 generated_at=2026-10-20T00:55:22.780395+00:00（台北 08:55），数据 close=11.5、pct_chg=0.7888%、vol=1111850.79 手、amount=1281599.06332 千元；仅来自 Tushare 单一提供者，未做独立行情交叉核验、历史或流动性研究。

每次 Market run 的 artifact 为 market-report-<run_id>-1，保留 14 天；如需长期保存请及时下载。主项目已保存三次报告并核对，路径为 outputs/acceptance/20261020/github-market/{fixture,tushare,tushare-retry}/market-report-<run_id>-1/report.json（本机忽略目录）；本文件的脱敏摘要和链接长期入 Git。报告仅用于管线验收，不放入真实机会研究。

后续：正式规则具体内容仍待提供；按 AGENTS 和 docs/deployment.md 接手，业务变化遵循 spec → task/code → version → CHANGELOG。当前不把 Tushare Secret 传给 Cloud 开发任务，不自动上传 Drive。

## 本次云端验收 — 2026-10-20

本节是本聊天中实际执行的结果，历史 Actions/API 证据仍保留于上表。本次没有再次调用真实行情 API，也没有重跑或重新部署 workflow。

### 环境与基线

- 实际仓库：`zhiweiofli/opportunity-runtime-market-sensor`，目录 `/workspace/opportunity-runtime-market-sensor`；origin 的主机与仓库路径核对一致。
- 实际挂载 Environment ID：`ccarenv_b64_Y2NhcmVudl9mOGEyNzYzNzI4MDA4MTkxYmIwZGQyM2MwNGQ5ODk2Nw`。环境等待工具返回 ready，后续状态为 running / connected；离线命令确已执行。
- 交接文件中的 Environment ID 为 `ccarenv_b64_Y2NhcmVudl9iZGYzYmMyMmVkMWM4MTkxOTU1MDRiYWNjOGJlZjk2Yg`，与实际挂载 ID 不同。本次核实的是当前环境内的指定仓库，没有借用其他项目仓库；不将本次结果作为旧 ID 可访问的证明。
- 初始检出分支 `work`，commit `cfc65c27fa084cd232dd037d4717687dc7f17aa3`，工作区干净。
- 通过已连接 GitHub 工具核对 `main` 为 [`e0792a73f6afa41269f10308d16d9b0f8361a900`](https://github.com/zhiweiofli/opportunity-runtime-market-sensor/commit/e0792a73f6afa41269f10308d16d9b0f8361a900)。比较结果为 ahead 2 / behind 0，仅 README、cloud-handoff、validation 三份文档变化，运行代码不变。
- Git 远端代理不可用，因此通过 GitHub 工具读取上述提交、树及变更文档，核对 Git 对象 SHA 后导入本地；`git merge --ff-only e0792a73f6afa41269f10308d16d9b0f8361a900` 退出 0，将本地 `work` 快进到这一真实 main commit。下表为快进后重新执行的结果。
- 本次没有通过 CLI 创建另一云端任务，无新的 CLI 提交回执或可核实任务 URL，不虚构任务 ID；本节记录当前聊天的云端执行事实。

### 命令与结果

执行解释器为 Python 3.12.14，Market 代码仍仅依赖标准库。

| 实际命令/检查 | 退出码 | 结果 |
| --- | --- | --- |
| `python3 -m unittest discover -s scripts/market -p 'test_*.py' -v` | 0 | 8/8 通过，0.013s |
| `python3 scripts/market/market_sensor.py --source fixture --demo-abs-pct 5` | 0 | `SIGNALS: 2 demo signal(s); outputs/market/report.json` |
| `python3 - <<'PY'` 读取报告并断言（核心代码见下） | 0 | SIGNALS、3 observations、2 signals、task_version=0.2.0、demo_only=true、research_eligible=false；逐条 Signal 的演示/不可研究标志也通过 |
| `cmp .github/workflows/market-sensor.yml tasks/github-actions/market-sensor.yml`；快进后再次用 Python 字节比较 | 0 | 两份副本完全一致，SHA-256 为 `4cb3e4d1be1e237d3c5079ce9378f370d3ece74bdd442ab59ec230bffad9cbb3` |
| Python 读取两份生效 YAML，使用环境已有 PyYAML BaseLoader 做静态断言 | 0 | 只读权限、手动输入、Secret 引用、带引号参数、错误报告 artifact、离线 push/PR CI 与无 Market schedule 均符合约定；未新增项目依赖 |
| Python 读取 `docs/source-import.json` 并计算 SHA-256 | 0 | PROJECT_GUIDE 与六份导入原稿共七份文件均匹配原始摘要 |
| `git check-ignore outputs/market/report.json` | 0 | 报告处于忽略目录，不纳入 Git |
| `git diff --check` | 0 | 文档补丁无空白错误 |
| `git ls-remote --exit-code origin refs/heads/main`（含环境 running 后复核） | 128 | `Failed to connect to proxy port 8080`；Git 传输受阻，main 改由 GitHub 工具核实，没有绕过代理 |
| 后续排查：为同一 `git ls-remote --exit-code origin refs/heads/main` 命令启用执行工具的网络权限 | 0 | 沿用原代理成功读取 `refs/heads/main=e0792a73f6afa41269f10308d16d9b0f8361a900`，Git 只读远端访问已验证恢复 |

后续代理排查：HTTP_PROXY / HTTPS_PROXY 指向 `http://proxy:8080`，Git 无单独代理覆盖，环境策略允许 github.com，环境报告 running / connected、网络策略 enforced。默认受限执行中 TCP 检查返回 `Operation not permitted`；使用执行工具的命令级网络权限后，Git 通过原代理成功访问 GitHub。当前可用修复是为联网 Git 命令启用网络权限，无需修改代理、凭据或绕过代理；这不表示默认受限执行的网络权限已永久改变。此前失败保留为历史事实。

报告断言的核心代码实际以 Python heredoc 执行：

```python
import json
from pathlib import Path
r = json.loads(Path('outputs/market/report.json').read_text())
assert r['status'] == 'SIGNALS'
assert len(r['observations']) == 3
assert len(r['signals']) == 2
assert r['task_version'] == '0.2.0'
assert r['demo_only'] is True
assert r['research_eligible'] is False
assert all(s['demo_only'] is True and s['research_eligible'] is False
           for s in r['signals'])
```

该报告 generated_at=`2026-10-20T01:06:34.212207+00:00`（Asia/Taipei 09:06:34）。fixture 为 20261016 合成数据，涨跌幅 +6% / -5% 的绝对值命中、+1% 未命中；这只验证演示管线。

静态配置检查确认：两个 workflow 均为 `permissions: contents: read` 且无 job 级覆盖；Market 仅 workflow_dispatch，输入 source（fixture/tushare，默认 fixture）、trade_date、ts_code、demo_abs_pct（默认 5）。四项输入先映射 env 再以带引号参数传入脚本，TUSHARE_TOKEN 仅为 `${{ secrets.TUSHARE_TOKEN }}` 配置引用。artifact 步骤使用 `always()`、指定本次 report.json、缺文件报错、保留 14 天，并以 run_id/attempt 命名。此检查只读取仓库 YAML，不读取任何 Secret 值，也不替代本次未执行的 Actions 运行。

已有八项测试覆盖包含边界值的演示筛选及 Signal 协议、NO_MATCH/NO_DATA 区分、非法参数在抓取前失败、缺凭据不连接/不回退、模拟 daily 请求与字段归一化、上游错误脱敏、坏数据拒绝，以及运行错误覆盖旧成功报告。API 测试仅使用测试代码中的虚构凭据和模拟响应，没有读取真实 token。错误 artifact 的本次证据是上述静态配置加本地错误快照测试；历史真实 Actions 错误 artifact 证据仍为上表 run。

未发现本任务范围内需要修改的可复现代码缺陷；因此仅补验证记录，不新增测试、不改代码/task/workflow、不提升业务版本。原始临时报告与工具同步材料不提交 Git，仅保留本节脱敏摘要。

### 仍未验收的正式规则

正式市场范围、标的池、历史基准、异常指标与阈值、运行频率仍待用户明确。输出继续 demo_only=true / research_eligible=false；不进入真实机会研究，不签正式策略、交易或行情定时验收。显示/操作时区沿用 Asia/Taipei，报告保留带时区的 UTC 时间。

## 0.3.0 历史量价监测试运行 — 2026-10-20

本节记录新授权范围，前面的0.2.0记录保留为历史；不再以旧版未给参数阻止新需求。开发分支 `codex/market-history-v1`，合并后 main 基线 `2331743`，需求提交 `dcf82e3efa36167bb2af4a2f4c35322ff3a10ec3`。初始工作区干净；正常 fetch 并检出该分支，没有改代理/凭据或重构Git对象。远端 fetch 配置最初未包含需求分支，随后显式 fetch 该分支并成功检出。

### 云端离线证据

- Python 3.12.14；`python3 -m unittest discover -s scripts/market -p 'test_*.py' -v` 退出0，31/31通过（原八项仅更新实际生成版本断言，新增23项）。计算和测试仅依赖标准库；没有读取真实Tushare token。
- `python3 scripts/market/market_sensor.py --source fixture --demo-abs-pct 5 --output outputs/market/demo-report.json` 退出0，3 observations / 2 demo signals，task_version=0.3.0，demo_only=true / research_eligible=false；JSON/Markdown均生成。
- `python3 scripts/market/market_sensor.py --mode history --source fixture --as-of-date 20261016` 退出0，1552条合成历史 / 6代码 / 1候选。顺序状态为 MATCH、NO_MATCH、LOW_LIQUIDITY、NO_DATA、INSUFFICIENT_HISTORY、STALE_HISTORY，coverage_complete=false。样本与计数不代表真实行情。
- 独立数值期望：最后两日各+5%，R5分别0.05、0.1025；当前成交倍数3、此前60日成交额中位数1亿元、此前20日均额1.1亿元。252历史基准严格在各评价日前，当前日计数252/252；分位边界250/252通过、249/252未通过，额外100样本核对精确99%边界。相等计入，未复权close跳变不改变收益。
- 使用环境已有PyYAML BaseLoader检查两份workflow副本、只读权限、15分钟超时、台北cron/timezone；配置 SHA-256 `265cce06dfdcb793e83e8b9cd23251dc63cf6c3cf4d190f16992bb891f4fb5c3` 与报告一致。PyYAML只用于本次检查，不是运行/单测/CI依赖。
- PROJECT_GUIDE与六份原稿的SHA-256继续匹配source-import.json；公共Signal协议只补Market模式说明，不提升公共协议或其他角色版本。`git diff --check`退出0。
- 中文报告已打开核对：覆盖/失败、配置哈希、候选指标、事实/推测、人工下一步及JSON原始行定位齐全。所有输出留在忽略目录，不提交Git。

| 验收项 | 本轮实际证据/状态 |
| --- | --- |
| V1-01 兼容 | 原8项测试与旧demo CLI通过；生成版本0.3.0，旧报告不改写 |
| V1-02 正例/单位 | 独立合成历史、十进制复合收益/此前基准/中位数/千元转元核对通过 |
| V1-03 反例 | 单次命中、当前不命中、反向、低流动性和全零均不输出；保留过滤原因 |
| V1-04 边界 | 5%/99%/2倍/1亿元相等及略低、偶数中位数通过 |
| V1-05 防未来 | 三个评价日基准均排除自己/未来，改变未来不影响固定评价；越界API行报错 |
| V1-06 历史/日期 | 258/259行、目标日缺失、7/8天与120/121天跨度、未来日期通过 |
| V1-07 错误 | 乱序归一化；重复/坏代码/缺字段/非有限或布尔值/缺Secret/网络/写入错误均拒绝；错误快照清空候选，写失败清理两份文件 |
| V1-08 批次 | 6混合状态、6命中截断5、配置名单去重、四级稳定排序/ID、20代码离线批次通过；未签20代码真实网络完整运行 |
| V1-09 Actions | event选择离线通过：schedule无视dispatch inputs，固定history+tushare，日期取运行时台北日；手动默认demo、历史显式日期；YAML静态通过，平台解析另记 |
| V1-10 真实历史 | 待开发分支runner实跑；不以单日旧API或合成历史代签 |
| V1-11 自然定时 | 未执行；必须合并默认分支后观察真实schedule run，本PR不合并，不等待定时阻塞交付 |
| V1-12 人工交接 | 中文报告与JSON追溯离线核对通过，research_eligible=false；未补机制/独立可靠性/成本证据，不交真实Research |

串行节流与重试使用虚构时钟验证：两个临时失败后成功，等待2/5秒，下一正常请求再间隔2秒；总请求上限3次，API拒绝不重试，错误不含虚构凭据。20代码测试仅证明离线批处理/截断与覆盖逻辑，15分钟下的20代码真实网络运行尚未实测。

## 需求纠偏（revision 2，尚未完成新业务验收）

用户要求修正定位偏差并明确优先美股。旧6股量价方案的31项离线/CI仅为技术原型证据，不能签完整Market V1；旧规则退出生产默认、重复滚动收益不作独立持续性证明、取消人先补机制的前置研究要求。新规格见market-v1-requirements.md：首条US国内股票基金Flow Shift，ICI估计净流向、具体机制/工具证据和R1交接；尚待实现/数据预检/实跑，不因新文档声称已部署。

本机直接HTTP预检：ICI combined为403；SPY发行人页IncompleteRead。检索资料可读不等于原生采集可用；云端/Actions另验，无法取数须BLOCKED，可用合法原始快照人工输入回退（不把人工供数算自动），不扩大采集基础设施或购买权限。原始预检回执保存在主项目忽略目录outputs/acceptance/20261020/us-market-source-preflight/result.json。

## 0.3.0 revision 2：美股 Flow Shift → R1（2026-10-20）

**本节为当前业务范围；此前六股量价及其V1测试编号仅为已撤回原型的历史技术记录，不再签当前Market V1验收。** 按用户指令正常fetch并ff到需求提交 `66640ce03355b18a990ef78a76d1071b9088b249`，保留930a1b8现场与同一PR #2，未reset/丢改动、未合并或部署main。任务/code/workflow仍为未发布0.3.0。

### 来源预检与真实业务反例

- 云端实际正常HTTPS预检：ICI combined与State Street SPY原始HTML均为URLError，未取得有效正文；当前restricted网络规则未列两主机。不是已核实的来源端403，也不把检索可读当Python原生接入成功。预检元数据在忽略目录 `outputs/us-flow-preflight/`。
- 产品live CLI实际执行：`python3 scripts/market/market_sensor.py --mode flow --input-mode live_http --output outputs/us-flow-live/report.json`，退出0，status=BLOCKED、signals=[]、eligible=false，两源coverage均BLOCKED。as_of=`2026-10-20T06:13:40.537024+00:00`；JSON、中文report.md与阻塞packet均生成。BLOCKED非ERROR，不能解释为无信号；没有换URL绕过限制或使用第三方JSON。
- 通过连接的公开参考工具核对[ICI 2026-10-14发布](https://www.ici.org/research/stats/combined_flows)及其已公开链接的[打印PDF](https://www.ici.org/node/57009/printable/pdf)。Domestic equity最近四周：9/16=-11490、9/23=5696、9/30=-7282、10/7=-18355（USD million）。前两周符号相反，**不是本规则反转**；两区间净额-5794/-25637，差额-19843。此反例只证明业务判定，原生HTTP/原始HTML解析仍BLOCKED。
- 可复核数字保存在 `examples/us-flow-public-reference.json`，明确reference_only；没有把检索文本重建成“原始HTML”，该JSON不能作为生产数值输入。公开基金数据是周估计、可能修订，不是月度实际或已证实股票买卖。
- Tushare美股us_daily权限/SPY覆盖/volume单位真实预检 **NOT_RUN**：只允许runner持既有Secret；云端未读取真实token。已实现独立runner探测，API即使可响应也不推定ETF身份/成交量单位，不能据此冒充流动性通过。

### 实际离线运行与产物

Python 3.12.14，`python3 -m unittest discover -s scripts/market -p 'test_*.py' -v`退出0，**50/50通过**（31项既有回归+19项US/runner合同测试）；旧测试中定时/eligibility断言随revision 2纠偏，原8项demo回归保留。运行与测试只依赖标准库。

| 命令/检查 | 退出码 | 实际结果 |
| --- | --- | --- |
| `python3 scripts/market/market_sensor.py --mode flow --input-mode synthetic_fixture --as-of 2026-10-20 --output outputs/us-flow-synthetic/report.json` | 0 | 4周+3000/+3000/-4000/-4000，区间+6000/-8000、差额-14000 USD million，1个outflow_reversal示例，demo_only=true / eligible=false；三份报告、来源manifest和两份哈希原文保存 |
| `python3 scripts/market/market_sensor.py --mode flow --input-mode supplied_snapshot --snapshot-manifest outputs/us-flow-synthetic/source-manifest.json --as-of 2026-10-20 --output outputs/us-flow-replay/report.json` | 0 | 同一规范化指纹 `7bfc6b5af06c2e2749df51cb140c57a2372b48e1040f3be7922552012cf5ec17`；重放仍synthetic，不因改输入模式放行 |
| 原有demo CLI/历史fixture回归 | 0 | 原demo 3输入/2演示输出；历史原型仅legacy_demo，非生产默认，eligible=false |
| `python3 -m compileall -q scripts/market`、`git diff --check` | 0 | 编译及补丁检查通过 |
| Python读取两份YAML/配置及source-import摘要 | 0 | 周五08:17 Asia/Taipei、flow/live_http默认、只读contents/actions、9项手动输入、副本一致；PROJECT_GUIDE与六份原稿SHA-256未变 |

生产配置SHA-256：`b762b0cafa11f705f9bbca997dbeca0540dd7cc8f6575f8db462b20ab5f16200`。旧六代码配置移到config/legacy-market-history.json，生产配置不含universe。示例packet实际打开核对，位置 `outputs/us-flow-synthetic/researcher-packet.md`；可用README命令重建，不提交临时产物到Git。

合法真实快照模板为 `examples/us-flow-snapshot-manifest.example.json`：必须填原始HTML、canonical来源URL、实际带时区取得时间和字节SHA-256；当前仓库不包含伪装真实的发布快照。未取得真实原始文件前，不能用模板或合成文件签真实supplied_snapshot数据验收。

| 用例 | 当前证据与界限 |
| --- | --- |
| US-01 定位 | 默认/配置/任务均US Flow Shift；旧6股仅legacy，真实合格来源门槛通过才eligible=true交R1，不再要求人先研究 |
| US-02 正反例 | 双向反转、单周翻转、持续同向、零值、区间不足离线通过；四周不重叠，与滚动收益无关 |
| US-03 金额 | 两区间恰5000通过、略低拒绝；逗号/小数/负号/括号负数/缺值测试通过；单位漂移BLOCKED，不造历史分位 |
| US-04 原始源解析 | HTML契约/登录/类别/单位漂移离线通过，单位绑定具体表前标签；真实原始HTML尚未取得，native接入BLOCKED，未签全项通过 |
| US-05 时间 | 重复/缺周、排序、未来/陈旧发布、14/15日新鲜度、unknown日期、纽约日终精度与3月/11月DST边界通过 |
| US-06 修订/PIT | 取得晚于as_of拒绝；相同指纹复用原Signal/Generated At，修订生成新观察；旧/新原文按内容哈希同时保留；缺前次报告dedup未核实 |
| US-07 工具 | 发行人身份/USD/同日Closing Price与Shares、1亿美元恰等/略低、NAV/AUM/错单位/异日/陈旧/未来反例离线通过；真实完整发行人HTML及Tushare预检未签通过 |
| US-08 交接 | 合成完整正例到独立R1 packet且false；模拟真实来源合同全部门槛通过时true，缺门槛BLOCKED；这是逻辑测试，不是实际真实Signal验收 |
| US-09 故障 | 原8项demo及legacy回归、HTTP403/URLError、坏manifest/哈希、旧快照覆盖、第三份packet写失败清理三份报告和脱敏通过 |
| US-10 Actions | schedule/dispatch参数、周频时区、只读权限、native artifact恢复及完整保存静态/离线通过；实际新版本dispatch/产物与首个自然schedule分开待验 |
| US-11 业务案例 | 合成完整正例已读packet，公开真实发布数字反例已核对；真实原始抓取/解析受阻，不把参考核对代签原生源运行 |

公开源live没有取得合法响应，因此本轮交付的是可审查实现、真实BLOCKED报告、快照回放路径和清楚边界，不签“完整美股数据源已上线”。合并后首个自然周频必须另有真实run回执；不等待定时阻塞PR交付，不自动合并或交易。
