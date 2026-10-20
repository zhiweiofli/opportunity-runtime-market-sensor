# Opportunity Runtime · Market Sensor

Market Sensor 的独立私有仓库，使用 **GitHub Actions + Python + Tushare Pro**。需求来源为 [完整项目指南](PROJECT_GUIDE.md) 和 [Market 业务原稿](docs/03-market-sensor.md)；本仓库只实施 Market 组件。

当前业务版本 `0.2.0`：可验证数据接入与筛选管线，所有规则/输出仍为演示，`demo_only=true`、`research_eligible=false`。正式异常规则尚未确定，不能据演示结果生成真实机会或下单。

## 本地验证

Python 3.9+，只用标准库：

```sh
python3 -m unittest discover -s scripts/market -p 'test_*.py' -v
python3 scripts/market/market_sensor.py --source fixture --demo-abs-pct 5
```

应得到 8 项离线测试通过、3 observations 和 2 条演示 Signal。默认报告 `outputs/market/report.json` 每轮覆盖；保留历史时用 `--output` 指定不同路径。outputs、环境文件和 Python 缓存不入 Git。

## GitHub Actions

- **Market CI**：每次 push/PR 自动执行离线测试和 CLI 管线，无密钥、无真实行情调用。
- **Market Sensor**：Actions → Market Sensor → Run workflow。首次保持 `source=fixture`、`demo_abs_pct=5`，日期/标的留空；成功后下载 `market-report-<run_id>-<attempt>` artifact。
- **真实 API 接线**：仓库 Settings → Secrets and variables → Actions 新增 `TUSHARE_TOKEN`，再选 `source=tushare`，填本人核实的 `trade_date=YYYYMMDD`、单一 `ts_code` 和演示阈值。token 不能放到普通变量、输入参数或聊天。
- `SIGNALS` / `NO_MATCH` / `NO_DATA` / `ERROR` 含义不同。NO_DATA 不能证明休市；真实数据命中演示阈值仍不是可研究的真实机会。
- 传输采用 HTTPS；实连失败要处理权限/额度/可达性，不降级明文传 token。
- 暂无正式定时行情任务；台北 `Asia/Taipei` 是用户指定显示/操作时区，现有 JSON 的 generated_at 为带时区的 UTC 时间，可直接换算。

执行结构在 [.github/workflows/](.github/workflows/)；保留原位置 [任务模板](tasks/github-actions/market-sensor.yml) 供项目导航，修改时保持与生效 Market workflow 一致。CI 与 Market 均只读仓库权限，不自动提交行情数据或上传 Drive。

## Codex Cloud 接手

先选择本仓库对应的 Cloud environment，然后读取 `AGENTS.md`、`PROJECT_GUIDE.md`、`docs/deployment.md`、Market 原稿与当前验证记录。验收命令即上面的本地测试和 fixture CLI。无需数据库、队列、MCP 或 API Key 才能开发离线管线。

Cloud 执行不应获得 Tushare Secret；真实 API 验证在 GitHub Actions 里进行。正式规则未定时保持演示边界，需求变化按 spec → task/code → version → CHANGELOG。各阶段实际状态见 [验证记录](docs/validation.md)。
