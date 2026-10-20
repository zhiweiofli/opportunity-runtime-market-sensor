---
task_id: market-sensor
version: 0.3.0
platform: github-actions
role_spec: docs/03-market-sensor.md
implementation_spec: docs/market-v1-requirements.md
role_spec_status: reviewed
guide_basis: PROJECT_GUIDE.md §3.3, §6, §14, §19
updated_at: 2026-10-20
---

# Market Sensor：历史量价监测试运行

确定性 Python 执行 fetch → validate → calculate → filter → report；不让 LLM 扫描行情。业务原稿保持原文，精确定义以 [V1需求](../../docs/market-v1-requirements.md) 为准，数据/调度依据见 [官方资料](../../docs/market-data-references.md)。本轮默认值是获授权的工程试运行选择，不是投资偏好、错价证明或已验证交易策略。

## 两种入口

- `--mode demo`（默认）：兼容原 fixture / 单日单代码 Tushare 命令，显式 `--demo-abs-pct`。所有结果 demo_only=true；fixture 为20261016的三条合成记录。
- `--mode history`：按 [版本化配置](../../config/market-v1.json) 对固定6代码名单串行取数，最多20去重代码。可显式 `--as-of-date YYYYMMDD` 重放，默认是执行时 Asia/Taipei 当日。独立历史 fixture 也是合成材料，不能当真实行情。
- history 不接受 demo 的 trade-date、ts-code、demo-abs-pct；手动表单按 mode 选用对应字段，历史名单由版本化配置决定。

## 历史计算与过滤

向目标日前查询550自然日，至少259有效日线。5日收益由 pct_chg 复合，绝对值>=5%且相对每个评价日前252个 abs(R5) 的经验分位>=99%；成交额相对此前60个有效日中位数>=2倍。目标日必须命中，最近3个观察至少2次同向命中；最近3次跨度<=7自然日、最近60次跨度<=120自然日。此前20个有效日均成交额>=1亿元且当日成交额>0。amount 从千元乘1000转为元，不代表净流入。

基准排除评价日及未来；日期、代码、重复、有限数值和 pct_chg>-100 严格校验。目标日无行记 NO_DATA，不借旧行情冒充今日，也不解释成已确认休市。按分位、abs(R5)、成交倍数降序，代码升序；稳定 ID 为规则/日期/代码，最多5候选，披露总命中和截断数。不建设跨运行去重数据库。

逐标的状态：MATCH / NO_MATCH / NO_DATA / INSUFFICIENT_HISTORY / LOW_LIQUIDITY / STALE_HISTORY / ERROR。仅 MATCH / NO_MATCH / LOW_LIQUIDITY 算完成评估。完整范围、失败名单及 coverage_complete 始终披露。整轮状态 SIGNALS / NO_MATCH / NO_DATA / INSUFFICIENT_DATA / ERROR；任何取数或契约错误都非零退出、整轮 signals 为空，保留其余诊断。

真实历史为 demo_only=false、rule.status=trial；所有 fixture 和旧 demo 为 demo_only=true。所有候选 research_eligible=false。保留公共 Signal 字段、R5/分位/样本数/成交倍数/均成交额/逐日命中和历史范围。Possible Mechanism 明示待验证推测；人工补齐机制、可靠性和研究条件前，不交真实 Research，不提供买卖、仓位或目标价。

## Actions、Secret 与报告

生效 `.github/workflows/market-sensor.yml` 与本目录 yml 副本保持一致，contents:read，15分钟超时。手动默认 mode=demo / source=fixture / demo_abs_pct=5。历史合成重放需 mode=history / source=fixture / as_of_date=20261016；真实历史选 tushare 并填写核实的目标日期。

schedule 按 event_name 显式选择 history+tushare+版本化配置，不依赖 inputs 默认值。工作日台北20:17：cron `17 20 * * 1-5`，timezone Asia/Taipei。只有合并到默认分支后才会自然触发；可能延迟/丢弃，允许手动补跑，不加额外 scheduler。解析/自然触发是否通过，分别记录于 [验证记录](../../docs/validation.md)。

Secret 仅 runner 的 TUSHARE_TOKEN 环境变量引用；云端开发不读取或导出真实 Secret。只用 daily HTTPS，不依赖 trade_cal/stock_basic/daily_basic 或扩大权限。正常请求至少间隔2秒；30秒超时；仅临时传输错误额外重试2次，退避2/5秒；权限/契约错误不重试，不记录上游原始错误体。

每轮先清理旧快照，再写 `outputs/market/report.json` 和中文 `report.md`。JSON 保存实际配置/文件SHA-256、目标和请求区间、逐标的范围/行数/时间、完整有效 observations、覆盖及候选。Markdown 定位 JSON 的配置、逐标的记录、原始行和证据，分列事实、推测与人工下一步。任一写入失败非零退出并清理残留，不能上传上轮成功快照。`always()` 尝试保存两份报告到 `market-report-<run_id>-<attempt>`，缺文件报错，保留14天；不写行情到Git、不自动上传Drive。

根目录 [README](../../README.md) 提供可复制命令。旧八项测试继续保留，仅任务版本断言跟随0.3.0；V1-01至V1-12逐项证据见验证记录。代码/离线通过、真实历史手动通过与自然定时通过分别验收。
