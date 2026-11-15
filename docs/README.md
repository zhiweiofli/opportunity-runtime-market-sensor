# 原始业务规范与部署材料

`00-overview.md` 至 `05-judge.md` 与 PROJECT_GUIDE.md 从 Opportunity Runtime 当前项目导入，保留原文；来源 commit 和原始 SHA-256 在 source-import.json。本仓库仅实施其中 Market 组件，不据此创建其他角色 Runtime。

- [Market 原稿](03-market-sensor.md)：业务边界和正式研究触发条件。
- [部署约定](deployment.md)：本轮获授权范围、CI/手动 workflow、Secret 和 Cloud 边界。
- [验证记录](validation.md)：本地、GitHub、API、Cloud 分别记事实。

研究状态协调沿用完整项目：Final Status 为 KILL/HYPOTHESIS_READY/BLOCKED，WATCH 是阶段结果；Market 当前全为演示且不可研究。正式异常参数须先明确，再实现和单独验收。

## 机会闭环的增量设计

以下文档来自 Opportunity Runtime 根项目的工作区版本，描述用户提出的增量范围；原始业务文档保持不变。设计不代表流程或平台接入已经实现或验收。

- [GitHub 机会流程](github-opportunity-workflow.md)
- [独立实践 Agent 协议](practice-agent-contract.md)
- [实施与验收清单](github-workflow-implementation.md)
- [GitHub 接入核查](github-workflow-access-check.md)和 [Judge 交接草稿](judge-github-handoff.md)
