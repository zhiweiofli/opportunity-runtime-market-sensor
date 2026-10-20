# 原始业务规范与部署材料

`00-overview.md` 至 `05-judge.md` 与 PROJECT_GUIDE.md 从 Opportunity Runtime 当前项目导入，保留原文；来源 commit 和原始 SHA-256 在 source-import.json。本仓库仅实施其中 Market 组件，不据此创建其他角色 Runtime。

- [Market 原稿](03-market-sensor.md)：业务边界和正式研究触发条件。
- [部署约定](deployment.md)：本轮获授权范围、CI/手动 workflow、Secret 和 Cloud 边界。
- [验证记录](validation.md)：本地、GitHub、API、Cloud 分别记事实。

研究状态协调沿用完整项目：Final Status为KILL/HYPOTHESIS_READY/BLOCKED，WATCH是阶段结果。合成输入不能成为真实机会；合格真实Signal可交Researcher R1，不等于通过四Gate。

## 当前开发：美股Flow Shift（需求revision 2）

用户要求纠偏并明确美股优先。[新需求](market-v1-requirements.md)取代旧6股量价目标：从基金申赎与ETF净发行的行业估计中识别国内股票基金配置方向的持续反转，附具体机制、工具/流动性与R1 packet。参考页价值和口径风险见[页面评估](market-page-assessment.md)、[美股数据边界](market-etf-mechanism-references.md)。不复制仪表盘、不把EPS/估值/量价阈值当错价结论。

本分支930a1b8的量价代码作为旧原型保留，PR #2未合并；业务目标已撤回，不按其技术测试签完整Market V1验收。新实现和公开源实跑尚待完成，目标仍为未发布0.3.0，原六份文档不改写。
