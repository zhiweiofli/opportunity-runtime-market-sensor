# Opportunity Runtime · Market Sensor

Market Sensor 使用 **GitHub Actions + 确定性Python**，原始职责见 [项目指南](PROJECT_GUIDE.md) 与 [Market原稿](docs/03-market-sensor.md)。本分支未发布版本 **0.3.0** 按 [需求revision 2](docs/market-v1-requirements.md) 实现美股优先的 **Flow Shift → Researcher R1**，不做交易或新Runtime。

首条经济问题：美国Domestic equity基金类别的净新配置是否由连续流入变为连续流出，或反向变化，规模是否值得研究底层需求与定价压力？它使用ICI合并周度估计，不拿股票成交额替代基金流，也不声称已证实价格因果或错价。SPY只作相关类别的工具/流动性观测载体，不是交易选择。

## 输入与运行

Python 3.9+，运行/单测只依赖标准库，不需要把Tushare Secret交给云端。

```sh
python3 -m unittest discover -s scripts/market -p 'test_*.py' -v
# 生产入口：公开原始HTML；无参数时同样默认flow/live_http
python3 scripts/market/market_sensor.py --mode flow --input-mode live_http
# 完整合成正例：前两周各+3000，后两周各-4000，单位USD million
python3 scripts/market/market_sensor.py --mode flow --input-mode synthetic_fixture --as-of 2026-10-20
```

公开源403、传输失败、登录页、单位/类别漂移、缺工具事实或PIT资料时输出 **BLOCKED**，仍保存报告，不补造数据或写NO_SIGNAL。只有完整有效评估且未触发规则才为NO_SIGNAL；参数/程序/写出错误为ERROR并非零退出。当前云端实际公开HTTP为BLOCKED，不能把检索可读签成原生接入成功；实际记录见 [validation](docs/validation.md)。

合法取得的原始HTML可走 supplied_snapshot；无需用户先做机制研究：

```sh
# 先按模板填写实际取得时间、原始字节SHA-256，并放入两份未经改写的原始HTML
python3 scripts/market/market_sensor.py --mode flow --input-mode supplied_snapshot \
  --snapshot-manifest /path/to/snapshot/manifest.json --as-of 2026-10-20
# 重放已保存artifact中的来源（保留manifest与sources目录的相对位置）
python3 scripts/market/market_sensor.py --mode flow --input-mode supplied_snapshot \
  --snapshot-manifest outputs/market/source-manifest.json --as-of 2026-10-20 \
  --output outputs/replay/report.json
```

模板：[examples/us-flow-snapshot-manifest.example.json](examples/us-flow-snapshot-manifest.example.json)。`synthetic=false`仅适用于合法原始资料；模板占位符未填、缺元数据或哈希错误会BLOCKED。合成夹具即使用supplied_snapshot重放也永远demo_only=true / research_eligible=false，不靠改模式升级真实性。解析器支持ICI当前combined HTML表和发行人上市/同日价格/Exchange Volume (Shares)区块；未知格式含PDF不猜值，标BLOCKED，原始HTML完整接入仍须实测。

`--as-of`支持带时区ISO时间或YYYY-MM-DD（截至纽约该日结束）。源只有发布日期时，保守到次日纽约00:00才可用，自动处理夏令时。原始快照实际取得时间必须<=as_of；今天的修订历史不能回填过去。默认as_of取本次源采集完成后的实际时间，不编造精确发布时间。

## 规则与交接

[config/market-v1.json](config/market-v1.json)集中保存试运行参数：同一发布最近4个不同报告周、5–9天周间隔、前后各两周同向且方向相反、两区间净额绝对值分别>=5000百万美元，发布/工具数据新鲜度14天。SPY需官方上市/USD及同日价格和成交股数，美元成交额代理>=1亿美元粗筛；不是NAV/AUM，也不验证成本/容量。金额保留十进制字符串与单位，不造104周历史分位。

真实来源全部门槛通过时Signal为 **demo_only=false / rule.status=trial / research_eligible=true**，只授权进入R1核验Money/Mechanism，不代表已过四Gate、策略有效或可交易。夹具始终synthetic且false；旧量价也始终false。具体机制、反证/未知和原4周事实由Sensor包内给出，Researcher可KILL，不要求用户先补一份机制研究。

每轮写 `outputs/market/report.json`、中文 `report.md`、独立可读 `researcher-packet.md`，并保存 `source-manifest.json` 与内容哈希命名的 `sources/*.html`。packet内含原始URL、日期/精度、4周金额、哈希、工具事实、机制、反证及R1问题；合格真实包可人工存Drive Signals/Market，无自动上传服务。BLOCKED包与合成包不可冒充真实Signal。

同路径重跑自动读取前次JSON；也可传 `--previous-report /path/to/report.json`。相同稳定ID/数据指纹复用原Signal和Generated At，修订则新观察并记录revision_of。未取到前次资料明确dedup未核实，不宣称全局新证据。跨run应保留前次原始来源artifact；文件去重不建设数据库。输出与原始临时数据均不入Git。

## Actions与权限

[生效workflow](.github/workflows/market-sensor.yml)与[任务副本](tasks/github-actions/market-sensor.yml)保持一致。

- 手动默认flow/live_http，支持as_of；合成验收选synthetic_fixture并填2026-10-20。合法快照重放可填同仓库snapshot_run_id，前次去重可填previous_run_id，从原生artifact恢复manifest/原文和报告。若此前抓取本就BLOCKED，恢复artifact也不会凭空补齐数据。
- **每周五08:17 Asia/Taipei**，显式flow/live_http，忽略手动inputs；合并默认分支后才能自然触发，不能以手动通过代签。定时可能延迟/丢弃，保留手动重放。
- `contents:read`；新增`actions:read`仅用于恢复公开快照/前次报告artifact，没有写仓库、Drive或额外长期凭据权限。
- runner独立步骤可用既有Secret预检Tushare us_daily/SPY；无Secret/权限/覆盖或单位不明都不冒充通过。公开ICI/发行人抓取步骤不接收Tushare token，token只发到https://api.tushare.pro。云端不读取/复制该Secret；当前真实US权限预检未跑。
- CI仅离线：旧回归+US业务用例与合成packet。15分钟运行上限，always尝试保存三份报告、来源和预检到`market-report-<run_id>-<attempt>`，保留14天。写出失败非零且清除旧报告。

实际源/Actions阻塞和合并后待验项见 [验证记录](docs/validation.md)。当前PR不合并，不把配置提交说成已部署。

## Legacy兼容入口

原8项demo回归和历史原型保留，明确退出生产默认与当前Market V1验收：

```sh
python3 scripts/market/market_sensor.py --source fixture --demo-abs-pct 5
python3 scripts/market/market_sensor.py --mode history --source fixture --as-of-date 20261016
```

六代码配置在 [config/legacy-market-history.json](config/legacy-market-history.json)，真实数据运行也只是legacy/demo且eligible=false。重叠5日收益的多次命中不能证明排除了单次跳动。其他角色、公共协议版本、六份业务原稿和PROJECT_GUIDE保持原样。
