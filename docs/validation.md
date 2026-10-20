# Market Sensor 验证记录

业务版本：0.2.0。部署不代表正式异常规则或交易策略已验收。全部实跑基于部署提交 `cfc65c27fa084cd232dd037d4717687dc7f17aa3`。

| 阶段 | 状态与证据 |
| --- | --- |
| 私有 GitHub 仓库/推送 | 已创建并推送 [zhiweiofli/opportunity-runtime-market-sensor](https://github.com/zhiweiofli/opportunity-runtime-market-sensor)，main 分支 |
| 本地离线测试/CLI | Python 3.9.6，8/8 通过；fixture 3 observations→2 演示 Signal；YAML、导航、原始需求 SHA-256 核对通过 |
| Actions CI | [39350160142](https://github.com/zhiweiofli/opportunity-runtime-market-sensor/actions/runs/39350160142) 成功，Python 3.11 的 8 项测试与 CLI 报告断言 |
| Actions 手动 fixture | [39350184015](https://github.com/zhiweiofli/opportunity-runtime-market-sensor/actions/runs/39350184015) 成功，下载 artifact 核对 3 observations / 2 signals，版本 0.2.0、demo_only=true、research_eligible=false |
| 真实 HTTPS 首次尝试 | [39350190556](https://github.com/zhiweiofli/opportunity-runtime-market-sensor/actions/runs/39350190556) 缺 TUSHARE_TOKEN，ERROR / 0 Signal；错误报告正常保存，无合成数据回退 |
| Secret 修正/真实 HTTPS 重跑 | 用户在本仓库配置 Secret 后，[39350480874](https://github.com/zhiweiofli/opportunity-runtime-market-sensor/actions/runs/39350480874) 成功；下载核对 20261016 / 000001.SZ、1 条 observation、NO_MATCH / 0 Signal，source=tushare；demo_only=true、research_eligible=false |
| 正式规则/定时行情 | 用户将提供规则，具体市场/标的范围、历史基准、阈值、频率未收到；没有 schedule，不签正式异常识别/交易策略通过 |
| Codex Cloud | CLI 已有账户环境，但此次未找到本仓库环境；浏览器需要登录，用户自行初始化。尚未提交云端任务，不签云端执行通过 |

真实 API 输入为 source=tushare、trade_date=20261016、ts_code=000001.SZ、demo_abs_pct=5，只是接线样例，不是标的/规则决策。重跑报告 generated_at=2026-10-20T00:55:22.780395+00:00（台北 08:55），数据 close=11.5、pct_chg=0.7888%、vol=1111850.79 手、amount=1281599.06332 千元；仅来自 Tushare 单一提供者，未做独立行情交叉核验、历史或流动性研究。

每次 Market run 的 artifact 为 market-report-<run_id>-1，保留 14 天；如需长期保存请及时下载。主项目已保存三次报告并核对，路径为 outputs/acceptance/20261020/github-market/{fixture,tushare,tushare-retry}/market-report-<run_id>-1/report.json（本机忽略目录）；本文件的脱敏摘要和链接长期入 Git。报告仅用于管线验收，不放入真实机会研究。

后续：用户完成本仓库 Codex Cloud 环境初始化并提供正式规则后，按 AGENTS 和 docs/deployment.md 接手；业务变化遵循 spec → task/code → version → CHANGELOG。当前不把 Tushare Secret 传给 Cloud 开发任务，不自动上传 Drive。
