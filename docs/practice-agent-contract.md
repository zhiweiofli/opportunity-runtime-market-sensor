# 独立实践 Agent 交接协议 v1 设计

状态：待实现。目录与字段为实施契约，尚未创建实际运行入口。

## 目录与格式

```text
opportunities/<opportunity_id>/opportunity.json
opportunities/<opportunity_id>/decisions/<decision_id>.json
practice/inbox/<task_id>/task.json
practice/results/<task_id>/<run_id>/result.json
practice/results/<task_id>/<run_id>/report.md
protocols/practice.md
or-archive/manifest.json
site/data/latest.json
```

JSON 使用 UTF-8，时间为含时区 ISO 8601。schema_version 初版为 1。所有 ID 持久唯一，重跑沿用任务 ID，run_id 每次实际运行不同；机会身份按业务问题与目标客户归并，不能仅凭标题或相似词自动合并。路径必须为仓库内安全相对路径，校验禁止逃逸、重复 ID 和失效引用。

## PR 路径边界

业务 PR 的类型必须明确为 review、practice-result、decision 或 archive；implementation 留给代码及配置变更。review 可新增机会记录、实践输入和必要的 Research/Judge 镜像；practice-result 只能新增结果；decision 可新增决定及继续验证所需的新任务；archive 只能更新镜像。业务 PR 不得修改 workflow、校验器或既有任务、结果和决定，也不得删除这些记录。路径检查仅是第一道约束，还须校验内容、引用、审批证据和实际 GitHub 状态；路径检查通过不表示 PR 获准执行或合并。

## 机会记录

必填字段为 schema_version、opportunity_id、title、business_problem、target_customer、value_hypothesis、source_refs、research_status、judge_recommendation、critical_unknown、created_at、updated_at。经济数值保存 value、unit、basis（measured/estimated/unknown）及 evidence_ref；未知数值为 null。source_refs 必须保留 Drive Doc ID、来源更新时间、镜像路径和固定 commit，按可获得字段披露缺口。

人工决定是追加文件，含 decision_id、opportunity_id、action（launch/continue/pause/close）、reason、actor、decided_at、source_issue_comment_url，以及适用结果 run_id。暂停含恢复条件，继续含新任务引用，立项可附目标项目链接。权威版本以合并提交为准。

## 输入任务

必填字段为 schema_version、task_id、opportunity_id、question、hypothesis、success_criteria、falsification_criteria、deliverables、context_refs、budget、allowed_actions、stop_conditions、created_at。

- question 必须能通过实践回答；criteria 允许定性标准，但必须可核验。
- context_refs 指向具体版本的研究、Judge、历史结果和人类决定。消费者同时核对当前 main 上是否已有暂停/关闭/替代决定。
- budget 包含最大时长、允许费用与币种；未知预算须明确表示待人补充，不能推断无限额度。
- allowed_actions 明确允许的操作，涉及外部行动按原项目规则授权。
- 合并 PR URL、SHA、merged_by 从 GitHub 事实解析，不能信任 Agent 自填 approved=true。
- 已批准任务的实质修改再次走 PR；已领取时绑定 task 内容 hash。任务内容改变后旧运行停止并等待重新授权，不把最新上下文悄悄套入旧实验。

## 发现、领取、恢复

1. 定时同步 main，枚举有效 inbox，核对机会决定、已完成结果、开放结果 PR 与任务内容 hash。
2. 每个 task_id 对应一个任务 Issue，由中心端幂等创建并保存映射；重复触发复用既有 Issue。
3. 消费者在 Issue 提交结构化 claim 请求，含 task_id、task_hash、run_id、agent_id、请求时间。中心 Actions 串行处理领取请求，查询已有租约后发出确认回执。消费者等确认后才执行。
4. 不能用普通 assignee 或最后一条评论当原子锁。每任务 concurrency 串行化后，必须重新读取有效回执；处理触发采用重扫未处理请求，避免 Actions 合并排队事件导致漏领。
5. 初版默认租约 2 小时、每 30 分钟心跳；这是实现默认值，消费者可在任务预算范围内续租。过期显示待恢复，不能立即自动重复可能已有外部副作用的实验。
6. 中断后先按 run_id 查询结果与副作用日志，再恢复或请求人工处理。若外部消费者不能完成此握手，首次只做协议演练，运行状态保持未接通。
7. 暂缓/关闭即时由当前有效人类决定阻止新领取。运行中消费者在每次外部行动前及心跳时检查停止条件。

运行回执字段为 event_id、task_id、run_id、agent_id、task_hash、event_type（claim/accepted/heartbeat/blocked/released）、timestamp、lease_until、reason；accepted 由中心确认。请求与确认区分，中心只接受配置的消费者身份。以事件 ID 去重，重跑不得发重复确认。

## 输出结果与 PR

result.json 必填 schema_version、task_id、opportunity_id、run_id、task_hash、input_commit、started_at、finished_at、outcome、criteria_results、evidence_refs、actual_cost、remaining_unknown、recommendation。

outcome 为 supported/refuted/inconclusive/blocked；这是实验结论，立项由人决定。criteria_results 逐项对照输入标准；actual_cost 保存真实时长和费用，未知为 null。report.md 记录方法、实际操作、原始数据位置、反证、失败和可复现步骤。证据含采集时间、来源及内容摘要，有文件时附 hash。

PR 类型明确为 practice-result，关联任务 Issue 与输入合并 PR。同 task_id/run_id 重试更新已有分支和 PR。检查 main 是否已有该结果，避免重复归档。结果 PR 不允许擅自改任务预算、授权、人类决定或执行配置；需变更时另起明确提案。

结果 PR 合并后任务从已接受结果推导为完成，保留 inbox 原记录用于追溯；消费者跳过。结果 PR 关闭未合并时保留当前运行与原因，可补充后再提；不能直接当已完成。

## 提交与通知

评审 PR 与结果 PR 均关联机会 ID、任务 ID、证据版本，正文包含业务摘要、主要数据、关键未知和本次需人决定的事项。通过 GitHub reviewer/订阅机制通知人；个人账号共用提交身份时须实测通知行为，不能把创建 PR 成功等同于人收到通知。

Judge 的平台定时能力、GitHub 写入能力和实际授权必须分别验收。平台不能直接发 PR 时先保存完整提交包并明确失败，由已授权的 gh 执行端接力；不能把手工接力登记成自动交接。
