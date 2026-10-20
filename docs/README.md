# 原始业务规范与部署材料

`00-overview.md` 至 `05-judge.md` 与 PROJECT_GUIDE.md 从 Opportunity Runtime 当前项目导入，保留原文；来源 commit 和原始 SHA-256 在 source-import.json。本仓库仅实施其中 Market 组件，不据此创建其他角色 Runtime。

- [Market 原稿](03-market-sensor.md)：业务边界和正式研究触发条件。
- [部署约定](deployment.md)：本轮获授权范围、CI/手动 workflow、Secret 和 Cloud 边界。
- [验证记录](validation.md)：本地、GitHub、API、Cloud 分别记事实。

研究状态协调沿用完整项目：Final Status 为 KILL/HYPOTHESIS_READY/BLOCKED，WATCH 是阶段结果。Market 旧演示和所有 fixture 不可作为真实研究输入；0.3.0真实历史测量为 trial，仍须机制核验，research_eligible=false。

## 下一阶段：历史量价监测试运行

用户已授权补齐参数并启动开发。[Market V1 可执行需求](market-v1-requirements.md) 给出6代码名单、历史基准、复合收益/成交额阈值、持续/流动性过滤、台北定时、兼容与12项验收；接口/时区依据见 [资料核验](market-data-references.md)。本分支实现0.3.0，实际部署、真实历史与自然定时分别见验证记录，不能从代码版本推定已上线。原六份业务文档不改写。
