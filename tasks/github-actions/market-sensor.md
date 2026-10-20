---
task_id: market-sensor
version: 0.3.0
platform: github-actions
role_spec: docs/03-market-sensor.md
implementation_spec: docs/market-v1-requirements.md revision 2
role_spec_status: reviewed
updated_at: 2026-10-20
---

# Market Sensor：美股基金配置 Flow Shift → R1

确定性Python负责抓取、来源/时间校验、金额计算、规则及报告，不由LLM扫描行情。以[需求revision 2](../../docs/market-v1-requirements.md)和原Market/overview业务原稿为准。0.3.0为未发布开发版本，不因纠偏虚增0.3.1。

## 首条规则与门槛

`us_domestic_fund_flow_reversal_v1`：ICI combined周报Domestic equity类别，同一发布最近4个不同且不重叠报告周，间隔5–9天。前2周各正、后2周各负或反向，两区间净额绝对值分别>=5000百万美元。零值、单周翻转、持续同向、物质性不足均不触发；不造长期分位。数据是共同基金净新现金流与ETF净发行的行业估计，可修订，不是全市场净流量或股票成交额。

发布日与数据取得时间分开：发布日期只有date时保守等纽约该日结束；源发布时间/快照实际可得时间均须<=as_of。发布和工具日期新鲜度14天，最新报告周距发布日<=14天。回放只使用当时已保存/合法提供的vintage；不把当前修订值回填过去，不猜精确发布时间。

SPY仅作相关类别观测载体。官方身份须为美国上市/USD；同一Fund Market Price日期的Closing Price与Exchange Volume (Shares)计算美元成交额代理>=1亿美元。不是NAV/AUM或全市场成交量，不证明滑点、容量、成本或已选交易工具。缺工具事实只保存Flow观察并BLOCKED，不换A股。

具体机制：基金申赎/份额发行方向变化可能改变底层股票边际配置压力。现金缓冲、实物申赎、其他持有人吸收、季节性、载体迁移、估计修订或预先定价均可证伪；不能将相关性叫价格因果或错价。

## 输入、输出与R1

默认 `flow/live_http` 正常请求ICI/发行人原始公开HTML，不带Tushare Secret，不抓第三方收藏站JSON。仅使用当前支持的HTML契约；登录、403、传输/格式/单位漂移均BLOCKED，不绕过限制、不买会员、不新增抓取服务。

`supplied_snapshot`使用合法原始HTML+来源URL+实际取得时间+原始字节SHA-256；支持本地manifest和原生artifact重放。`synthetic_fixture`含完整机制与工具正例，始终demo_only=true、eligible=false；改输入模式不能把夹具升级成真数据。示例/可复制命令见[README](../../README.md)。

来源、时间、反转/物质性及工具门槛全部通过的真实Signal：demo_only=false、rule.status=trial、research_eligible=true，只交Researcher R1核验Money/Mechanism，可KILL。用户不必先完成机制研究。不输出Hypothesis、买卖方向、目标价或仓位。未知的表达成本/工具匹配交后续研究，不假称四Gate已过。

每轮覆盖JSON、中文报告和researcher-packet.md，包内独立呈现4周日期/金额、区间变化、单位、估计/修订、URL/取得与发布日期/哈希、SPY事实、潜在机制、反证未知和R1下一问题。所有原始源按内容哈希保存到artifact；原始大页不入Git。真实合格packet可由人直接保存到Drive Signals/Market，不新增Drive服务。

状态为SIGNALS / NO_SIGNAL / BLOCKED / ERROR。缺数据不是NO_SIGNAL；观察材料进observations/coverage，不混入真实合格Signal。参数/程序/写出错误非零；BLOCKED仍写三份诊断。写失败清理残留，不上传上轮成功快照。

稳定ID含规则/最新周/方向，observation_id指纹含4周数值、发布日、配置/版本；前次JSON可提供或原路径重跑读取。相同观察复用原Signal/Generated At，修订创建新观察；未取得历史则dedup未核实。Researcher原观察键协议不变，无全局去重服务。

## Actions

每周五08:17 Asia/Taipei，cron `17 8 * * 5` + timezone，schedule显式flow/live_http，不使用手动空inputs。默认分支合并前不启用；自然触发另验，平台可能延迟/丢弃，保留手动重放。

手动flow输入input_mode、as_of、可选snapshot_run_id / previous_run_id。download-artifact使用内置GitHub token和新增actions:read，只为同仓库原始快照与前次报告恢复；缺前次报告不阻塞监测，但不能声称全局新证据。运行contents:read、15分钟超时；always尝试保存当前报告、packet、manifest、原文与runner预检，run_id/attempt唯一，保留14天。

Tushare美股权限/SPY覆盖/量单位单独runner预检，既有Secret只发api.tushare.pro。公开抓取步骤不接收该Secret；us_daily响应成功也不推定volume单位/ETF覆盖，不用于冒充流动性证明。真实预检没跑就记NOT_RUN，不将token拉入云端，不扩大接口权限或购买。

旧demo/history仍可显式选择；六股量价在legacy配置中，全部eligible=false，不再是正式目标。重叠收益不证明多个独立冲击。旧回归不代替US-01至US-11业务验收；实际分层证据、公开源BLOCKED及待验项见[validation](../../docs/validation.md)。不自动合并或交易。
