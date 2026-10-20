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

## 已授权的下一阶段

用户已授权由本会话完善需求并让云端开工，原“正式参数未定”的等待条件已由 [Market V1需求](market-v1-requirements.md) 解除。本开发分支已实现0.3.0历史量价监测试运行与定时配置；以上0.2.0边界保留为历史事实，不能用其禁止新授权范围。真实历史数据不再称合成演示，但统计候选仍须机制核验，不自动交Research。实际部署和自然触发分别验收，先交PR，不把配置已提交说成已上线。

- 手动默认 demo+fixture；history 模式按 config/market-v1.json 使用小名单和明确目标日。schedule 显式 history+tushare，不依赖手动 inputs。
- 工作日台北20:17，IANA timezone 配置；只读权限、15分钟超时、JSON/Markdown artifact 保留14天。首个自然 schedule 必须在默认分支合并后另验。
- 真实历史 API 可在开发分支 workflow_dispatch 验收，仅 runner 使用既有 Secret，不将其传给云端。受权限或平台限制时保留真实阻塞，不扩大接口或账户权限。
