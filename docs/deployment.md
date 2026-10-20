# Market Sensor 部署约定

本仓库是 Opportunity Runtime 的 Market 执行组件。完整项目指南与六份原始业务规范作为只读需求背景导入，固定平台分工不变。本轮用户授权新建私有 GitHub 仓库、推送指南及代码、部署 GitHub Actions，并尝试交由 Codex Cloud 开发。

- 行情抓取、校验、计算、筛选使用 Python；不使用 LLM 替代行情计算。
- 现有版本 `market-sensor@0.2.0` 的阈值是演示，所有输出继续 `demo_only=true`、`research_eligible=false`，不伪装正式策略。
- Market CI 在 push/pull_request 验证标准库离线测试和 CLI 管线；不需要 Secret，不调用真实行情。
- Market Sensor 使用 workflow_dispatch 手动触发，支持 fixture 与明确日期/单一标的的 Tushare daily。执行结果保存到 Actions artifact，人工交接，不自建 Drive 上传服务。
- Tushare token 只从 Actions Secret `TUSHARE_TOKEN` 或用户当前终端环境读取，不进入 Git、日志、Prompt 或 Codex Cloud 开发指令。没有 token 不能签真实 API 通过。
- 正式市场/标的/历史基准/阈值/频率尚未确定，不擅自新增正式规则、交易、自动资金动作或默认行情 schedule。
- Codex Cloud 必须绑定此仓库对应的环境；不能借用其他项目环境冒充切换成功。云端是否提交/运行及其输出另存证据，代码推送或 Actions 成功不等于 Codex Cloud 已运行。

验证以本地测试、GitHub commit/run/artifact、真实 API 和 Cloud 执行分别记录，见 validation.md。

## 已授权的下一阶段：纠偏后的美股Flow Shift

用户要求纠正量价原型偏差，已明确优先美股。当前执行以[需求revision 2](market-v1-requirements.md)为准；旧六A股、量价阈值、全false等待人工补机制及工作日晚间定时不再是生产目标。旧原型仅保留现场，PR #2未合并，新增定时未在默认分支启用。

新增ICI公开合并周报与已核对的工具身份/流动性证据作为原始来源；Tushare Pro保留现有入口，美股权限/ETF覆盖须预检，不能按A股daily成功推定。真实合格Signal进入Researcher R1，机制验证由Researcher承担，不新增人先研究的门槛。缺数据或工具证据仍不放行。

新周频为周五08:17 Asia/Taipei；业务实现、来源预检和自然触发分开记录。GitHub Actions+Python不变，不新增Runtime/Drive服务或交易；0.3.0仅为未发布目标，修订后再更新task/code/version/CHANGELOG并交同一PR审查。
