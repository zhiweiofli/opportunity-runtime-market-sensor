# Opportunity Runtime · Market Sensor

**开发范围已纠偏（需求revision 2）**：用户明确美股优先。[当前规格](docs/market-v1-requirements.md)是基于ICI基金净配置变化的Flow Shift → Researcher R1；下方6股量价实现/命令属于930a1b8旧原型，保留供复用，不作为完整Market V1或生产默认验收。新规格尚待实现，PR #2未合并。

Market Sensor 的独立私有仓库，使用 **GitHub Actions + Python + Tushare Pro**。原始边界见 [项目指南](PROJECT_GUIDE.md) 和 [Market 原稿](docs/03-market-sensor.md)，0.3.0 实现口径见 [历史量价监测试运行需求](docs/market-v1-requirements.md)。本仓库只实施 Market 组件。

当前开发版本 **0.3.0**：固定6代码历史量价监测，保留单日演示。真实 Tushare history 为 `demo_only=false`、`rule.status=trial`；所有 fixture 和 demo 仍 `demo_only=true`。所有统计候选 `research_eligible=false`，机制、可靠性及表达成本须人工核验，不是荐股或已验证交易策略。部署和自然定时实跑状态以 [验证记录](docs/validation.md) 为准。

## 离线运行

Python 3.9+，运行与单测均只依赖标准库，不需要真实 token：

```sh
python3 -m unittest discover -s scripts/market -p 'test_*.py' -v
python3 scripts/market/market_sensor.py --source fixture --demo-abs-pct 5
python3 scripts/market/market_sensor.py --mode history --source fixture --as-of-date 20261016
```

第一条包含原八项兼容测试与历史边界测试；旧 demo 为3 observations / 2演示输出。独立历史 fixture 为1552条合成记录，六个代码分别展示 MATCH、NO_MATCH、LOW_LIQUIDITY、NO_DATA、INSUFFICIENT_HISTORY、STALE_HISTORY，仅000001.SZ产生候选；这不是实际行情。

每轮覆盖 `outputs/market/report.json` 和中文 `report.md`，包含配置/摘要、逐标的覆盖/失败及原始数据定位。保留历史时用 `--output outputs/market/replay.json`（同时生成 replay.md）。输出、环境文件、Python缓存不入Git。语法解析错误在运行前退出；运行错误会写空候选错误快照；写入失败非零退出并清理残留报告。

## 真实历史与默认参数

配置集中在 [config/market-v1.json](config/market-v1.json)：6个种子代码、550自然日查询、252个此前历史样本、至少259行、5日复合收益绝对值>=5%且分位>=99%、成交倍数>=2、3次观察至少2次同向命中，以及流动性/新鲜度限制。阈值/名单是本轮试运行默认值，改动走 spec → task/code/config → version → CHANGELOG。

真实运行仅在已配置 Secret 的 Actions runner 中执行（开发云端不读取 Secret）：

```sh
python3 scripts/market/market_sensor.py --mode history --source tushare --as-of-date 20261016
```

省略 `--as-of-date` 时取运行时台北日期。目标日无记录记 NO_DATA，不借用旧日期、不确认休市；不新增日历或估值接口权限依赖。单日兼容入口为 `--source tushare --trade-date YYYYMMDD --ts-code 单一代码 --demo-abs-pct 5`，只用于 demo。

## GitHub Actions

- **Market CI**：push/PR 自动跑离线单测及两种 fixture CLI，无 Secret、无真实行情调用。
- **Market Sensor**：Actions → Market Sensor → Run workflow。默认 mode=demo / source=fixture / demo_abs_pct=5。历史合成重放选 history / fixture / as_of_date=20261016；真实历史选 history / tushare / 核实日期。
- 真实 Secret 仅使用仓库既有 `TUSHARE_TOKEN`，不放入普通变量、表单、聊天或开发云端，不更改权限/凭据。Secret 只注入抓取步骤；错误不会回显原始服务端内容。
- schedule 使用 `timezone: Asia/Taipei`，工作日20:17显式运行 history+tushare，默认日期为执行时当地日。合并到默认分支后才启用；延迟/丢弃可手动重放，不以手动实跑代签自然定时验收。
- 下载 `market-report-<run_id>-<attempt>` artifact，含 JSON 和中文Markdown，保留14天。ERROR 非零且整轮候选清空，仍尝试保存诊断；NO_DATA、INSUFFICIENT_DATA、NO_MATCH 互不等同，不构成“没有机会”的结论。

工作流只读仓库，15分钟超时；正常请求间隔>=2秒、30秒单次超时，临时网络错误最多额外重试2次。生效文件 [.github/workflows/market-sensor.yml](.github/workflows/market-sensor.yml) 与 [任务副本](tasks/github-actions/market-sensor.yml) 同步。实际规则、公式、覆盖状态、报告与人工交接细节见 [任务说明](tasks/github-actions/market-sensor.md)。无交易、新Runtime、数据库、自动提交数据或Drive后端。

## 云端开发与验收

[0.2.0历史交接材料](docs/cloud-handoff.md) 保留历史事实；本轮以 [0.3.0需求](docs/market-v1-requirements.md) 为准，参数等待条件已解除。先读 AGENTS、指南、原稿和部署约定。真实API只在runner验收，离线、手动Actions和自然定时分别记录，不把资料/代码准备完毕写成已上线。原稿摘要见 [source-import.json](docs/source-import.json)。
