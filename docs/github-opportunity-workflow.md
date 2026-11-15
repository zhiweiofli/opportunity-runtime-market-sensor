# GitHub 中心机会验证流程

状态：2026-11-15 用户确认方向，实施设计待 sol 执行。本文不证明功能已上线。

## 目标与范围

GitHub 汇聚研究、评审、验证任务、实践证据与人类决定。GPT Judge 通过 PR 提交评审，人合并后批准其中的验证任务；独立实践项目定时读取主分支输入，探索后通过结果 PR 回写，人验收后决定立项、继续验证、暂缓或关闭。Pages 呈现关键信息、数据和状态流转。

本仓库交付目录入口、协议、校验、状态投影与看板。实践 Agent 的实现、运行环境、定时设置属于独立项目。传感器与 Researcher 延续已有平台。Market 保持已记录的挂起与演示状态。

这是用户明确提出的新需求，对原指南中五角色、无看板的 V1 范围作增量补充。实践是外部消费者，原六份业务文档保留。Judge 沿用远端每三天、回看七天的约定。每周主动推进一个新机会的预算继续生效。

## 已核实基线

- 目标私有仓库 `zhiweiofli/opportunity-runtime-market-sensor`，默认分支 main。
- 2026-11-15 通过本机 gh API 核实 main 为 `c7aebc9cd70615e8a2234933ae9f7689e785bf81`。
- 远端已有 `or-archive/`、`site/` 和 Pages workflow。manifest 标记 78 份 Research、5 份 Judge 已镜像。
- 最近已检查 Pages run `43575263389` 在 configure-pages 失败；实施时重新诊断，当前公开站点可用性未签收。
- 本地根仓库没有 remote，且有既有未提交修改。`outputs/market-sensor-repo` 是独立仓库的旧开发分支工作副本。实施须从远端最新 main 新建隔离工作副本，不能将旧开发分支直接合入 main。
- 本地新 Sensor 规范比远端原始导入丰富。迁移只选实际需要的文件并保留来源，不能整目录覆盖远端。

## 主流程与授权语义

1. Gemini/Grok 采集，Gemini 研究，结果留在 Drive。原文的权威来源仍为 Drive，GitHub 保留带 Doc ID、更新时间的可追溯镜像。
2. Judge 读取新研究、历史机会、已合并实践结果和人类决定，去重后提交评审 PR。一个可独立批准的机会一个 PR；纯归档更新可以单独批量提交。
3. 评审 PR 包含机会记录、依据、建议及明确的验证任务。WATCH/DROP 可以归档，但没有实践输入任务。
4. 人合并评审 PR 后，任务随提交进入 `practice/inbox/`。消费者仅读取 main 上已合并的有效任务，Approve 按钮本身不触发执行。
5. 实践 Agent 按协议领取和执行，运行过程写入任务 Issue；最终产出结果 PR。失败、反证和证据不足都可作为完整结果提交。
6. 人合并结果 PR，表示接受记录。机会进入待决定；立项必须有单独明确的人类决定。
7. 人通过关联 Issue 的结构化决定评论选择立项、继续验证、暂缓或关闭。Actions 验证评论者身份和字段后生成决策 PR，人合并后更新权威机会记录。看板在此期间显示决定待入库。
8. 继续验证创建新任务 ID 并沿用机会 ID，任务随新的评审/决策 PR 获批。关闭或暂缓后的旧任务不得再次执行。

人类身份在实施时从实际仓库 owner/用户确认配置中解析。Agent 建议不得写作人类决定。若 Agent 与人共用 GitHub 身份，无法从 actor 独立证明审批者身份，必须披露这一限制并采用用户手动合并作为运行约定；需要强制隔离时配置独立 bot 身份。外部联系、费用、交易等沿用原授权边界，任务中写明具体允许范围。

## 状态模型

Judge 建议 NOW/NEXT/WATCH/DROP、Research 成熟度、工作流阶段分别保存。工作流阶段由已合并文件和 GitHub 事件计算。

| 阶段 | 进入证据 | 下一步 |
| --- | --- | --- |
| 待评审合并 | 开放的有效评审 PR | 人合并或退回 |
| 待领取 | main 中有效任务、无有效领取 | 外部 Agent 领取 |
| 实践中 | 领取被确认且未过期 | 心跳、阻塞或结果 PR |
| 实践阻塞 | 有效运行回执含阻塞原因 | 补输入或明确恢复 |
| 待结果验收 | 开放的有效结果 PR | 人验收或要求补充 |
| 待立项决定 | 结果已合并且无更新决定 | 人记录决定 |
| 已立项 / 暂缓 / 已关闭 | 已合并的人类决定 | 立项交接或等待恢复条件 |

关闭未合并 PR 只表示该提案未接受，不能自动关闭机会。要求修改结果 PR 时复用同一任务；明确启动下一轮验证才创建新任务。多任务机会逐任务展示，机会摘要优先呈现待人处理与阻塞项，不能靠单一状态掩盖并行任务。

## GitHub 能力分工

- Git、PR、Issue 保存版本、审阅与运行交流。
- Actions 校验结构/引用/状态、处理领取、归集事件、计算指标、生成和发布快照。使用托管 runner 执行短时确定性计算。
- Pages 展示静态数据，操作入口跳转 PR/Issue；浏览器不保存写仓库凭据。
- 主分支文件保存已接受的业务事实；Issue/PR 事件保存尚未合并的过程。页面数据可重新生成。
- 运行日志和临时大文件可以用 artifact；决定所依赖的长期证据必须有持久引用及摘要，不能只指向会过期的 artifact。

官方依据：[Actions](https://docs.github.com/en/actions/get-started/understand-github-actions)、[Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)、[分支保护](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)。具体账户可用性和通知仍需实测。

## 文档入口

- [实践协议](practice-agent-contract.md)
- [sol 实施清单与看板验收](github-workflow-implementation.md)
