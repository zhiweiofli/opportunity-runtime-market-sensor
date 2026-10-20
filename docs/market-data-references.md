# Market Sensor 数据与调度核验

核验日期：2026-10-20。范围：Tushare Pro 官方接口说明、GitHub Actions 官方文档；服务于固定小观察名单的 A 股日线量价异常检测需求。本文是资料核验，不是策略有效性验证，也不代替当前账户权限实测。

## Tushare daily

官方 [`daily` 文档](https://tushare.pro/document/2?doc_id=27)支持 `ts_code`、`trade_date`、`start_date`、`end_date`；日期格式为 `YYYYMMDD`，并提供单股时间区间调用示例。单次上限 6000 行，交易日约 15:00–16:00 入库；停牌日没有行情行。接口说明没有明确标注更新时间的时区，也没有用文字明确保证区间端点包含规则，因此上线验收应检查请求边界及返回日期，不能靠行位置猜日期。

该接口提供未复权 OHLC；`pre_close` 为除权昨收，`pct_chg` 基于它计算。`vol` 单位为手，`amount` 为千元，`pct_chg` 为百分数。因此 5 表示 5%，成交额转人民币元应乘 1000。字段还包含 `change`；盘后字段是可选项，本轮不需要。上述口径均来自同一份 [daily 字段表](https://tushare.pro/document/2?doc_id=27)。

对实现的推论：日涨跌使用源 `pct_chg`，不要用相邻未复权收盘价重新计算并声称两者等价；长区间价格水平比较会遇到除权跳变。若本轮只比较涨跌幅、成交量与成交额，不必因此引入复权数据接口，但必须保留口径并避免把异常解释为企业价值变化。252 个历史有效交易观测应排序、去重后取目标日前的数据；252 个自然日不能充当 252 个交易观测。当前固定名单的小规模历史请求可低频串行完成；全市场拉取则应遵循官方按日期获取的建议。

权限有文档差异：daily 页写基础积分可达每分钟 500 次；[官方权限总表](https://tushare.pro/document/2?doc_id=290)列出的 120 积分账户是每分钟 50 次、每日 8000 次，只覆盖非复权日线；2000 分以上仍需按各接口门槛判断。不能把 500 次当作本账户承诺。现有单股单日 daily 实跑只证明该请求成功；历史范围、返回完整性与额外接口均需独立验收。此任务不读取或调整账户积分、密钥和付费权限。

## 日历与可选接口

| 接口 | 当前官方说明 | 最小 V1 的取舍 |
| --- | --- | --- |
| [`trade_cal`](https://tushare.pro/document/2?doc_id=26) | 需 2000 积分；输入交易所、起止日期、`is_open`；返回 `exchange`、`cal_date`、`is_open`、`pretrade_date`。默认上交所，官方称三家股票交易所日历一致。 | 能精确区分休市与数据迟到；不能从 daily 成功推定日历权限。先验收权限；无权限时，明确目标日期并把空数据标为未知/待复核，不得假装已确认休市。 |
| [`stock_basic`](https://tushare.pro/document/2?doc_id=25) | 2000 积分起，每分钟 50 次，单次最多 6000 行；含代码、名称、上市状态和上市日期等。 | 固定人工维护的小名单无需动态全市场发现，故非必需；可在已确认权限后用于核对名单，不能暗中扩展范围。 |
| [`daily_basic`](https://tushare.pro/document/2?doc_id=32) | 至少 2000 积分，5000 分无总量限制；单次 6000 行，交易日约 15:00–17:00 更新；提供换手率、量比、估值和市值等。 | 仅用 daily 自算历史量价异常无需它。若后来要求换手率、自由流通股或估值筛选，再明确新增依赖与权限验收。 |

这三项是新增的接口权限依赖，并不表示必须单独付费购买；积分是否满足以及接口当前可用性均未在本次资料研究中实测。交易日历不可用时，工作流可以仍按固定日历频率触发，但不能据此保证交易日判断能力。

## GitHub Actions 调度与手动回退

[GitHub schedule 官方说明](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)目前支持在单条 cron 下指定 IANA `timezone`，默认仍是 UTC。台北可直接用 `timezone: Asia/Taipei`，不必再手动折算 UTC。该能力须经实际工作流解析与自然定时触发验收，文档存在不等于已部署通过。

定时文件必须在默认分支，并执行其最新提交。平台在高负载时可能延迟甚至丢弃排队任务，整点尤其繁忙；选择非整点只是降低风险，不能保证准时。公开仓库 60 天无活动还可能自动停用定时任务；当前私有仓库不应套用该公开仓库条款。不得把手动通过登记成定时通过。[来源同上](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

[`workflow_dispatch`](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch)应保留，便于重跑目标日期与验收指定分支；文件同样须先存在于默认分支。手动 inputs 的默认值只属于该触发方式，不能当作 schedule 运行时的输入保证。[contexts 文档](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#inputs-context)说明 `inputs` 属于手动或可复用工作流，缺失属性求值为空字符串。实现应按 `github.event_name` 明确选择手动输入或受版本控制的定时配置；不把空字符串传作代码、日期或阈值，也不要用通用 `||` 意外覆盖合法的 `false`/`0`。

最小验收需分别保存：离线边界测试、真实历史请求报告（请求日期和返回范围）、日历权限结果、工作流配置解析结果、手动 Actions 链接及首个自然 schedule 链接。未拿到后两项证据前，只能登记相应材料已准备或手动通过。
