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

### 机器可读约定

四种记录的具体类型及必填字段由 `schemas/workflow/` 中的 JSON Schema 定义。ID 仅使用字母、数字、下划线和连字符；引用使用仓库相对路径及完整 Git commit SHA。来源镜像字段无法取得时显式填 null 和缺口说明，不伪造 Drive ID、时间或版本。输入标准有稳定的 criterion ID，结果逐项引用它们。任务 hash 是原始 `task.json` 文件字节的 SHA-256 小写十六进制；计算前不重排 JSON 或转换换行。金额和时长以非负数及明确单位记录，未知值用 null，不视作零或无上限。

记录可选 `public` 对象是单独编写的脱敏标题、摘要与允许披露的细分摘要；缺失时公开投影不输出原始业务字段。公开的金额单独提供数值、币种、单位和 measured/estimated/unknown 标记，不带私有证据引用。它不构成发布授权：首次公开投影仍须确认字段符合现有公开范围。四 Gate 摘要与经济锚点是结构化字段，未知值明确标识。详情及原始证据保留在私有仓库。

## PR 路径边界

业务 PR 的类型必须明确为 review、practice-result、decision 或 archive；implementation 留给代码及配置变更。review 可新增或修改机会与实践输入，以及更新必要的 Research/Judge 镜像；任务的每次修改都须重新合并批准。practice-result 只能新增结果；decision 可新增决定及继续验证所需的新任务；archive 只能更新镜像。业务 PR 不得修改 workflow、校验器或既有结果和决定，也不得删除这些记录。路径检查仅是第一道约束，还须校验内容、引用、审批证据和实际 GitHub 状态；路径检查通过不表示 PR 获准执行或合并。

PR 正文必须且只能包含一行 `<!-- workflow-type: review -->`（类型按实际替换）。implementation PR 不得同时变更机会、实践输入、实践结果或历史镜像；业务数据与校验代码须分开审阅。检查器及依赖来自目标可信 base，提案分支只作为数据读取，不执行其中代码。初次引入该检查的 implementation PR 本身必须依靠人工审查及现有 CI，合并后此约束才会在后续 PR 上生效。

一个 review PR 只能包含一个机会的记录或任务；WATCH/DROP 不能新增或修改实践输入。一个 result PR 只能包含一次运行的结果与报告；一个 decision PR 只能包含一个决定和 continue 所需的一个新任务。纯镜像批量更新使用 archive 类型。

业务 PR 处理与结果追溯要求 GitHub 合并事实及合并时对应 head commit 上由 Actions bot 写入的 `opportunity/protocol/<PR编号>` 成功状态。由 Actions 自动创建的决定 PR 在同一工作流内完成等效预检并显式写入该状态，不依赖内部 token 触发后续工作流。评论编辑会使旧版未合并决定 PR 的状态失效并生成新版本。仓库保护规则若未要求该状态，人仍可绕过检查合并；消费者必须再次核验，不能仅因文件出现在 main 就执行。

成功状态记录校验时的 main SHA 和 PR 正文哈希；合并事实核验要求前者等于合并提交的第一父提交，并核对当前 PR 正文，以拒绝基线或类型说明变化后未经复核的结果。业务 PR 应使用 merge commit 或 squash merge；多提交 rebase merge 无法由该单一父提交证明校验基线，会被安全拒绝。已合并 PR 的正文如被编辑，也会导致后续证据核验失败，需恢复原正文或人工排查。main 有变化时重新检查所有带类型标记的开放 PR；仓库当前无法配置保护规则，因此仍存在检查重跑前人为强制合并的窗口，消费端继续拒绝不匹配记录。

## 机会记录

必填字段为 schema_version、opportunity_id、title、business_problem、target_customer、value_hypothesis、source_refs、research_status、judge_recommendation、critical_unknown、created_at、updated_at。经济数值保存 value、unit、basis（measured/estimated/unknown）及 evidence_ref；未知数值为 null。source_refs 必须保留 Drive Doc ID、来源更新时间、镜像路径和固定 commit，按可获得字段披露缺口。

人工决定是追加文件，含 decision_id、opportunity_id、action（launch/continue/pause/close）、reason、actor、decided_at、source_issue_comment_url，以及适用结果 run_id。暂停含恢复条件，继续含新任务引用，立项可附目标项目链接。权威版本以合并提交为准。

决定同时保存 `source_comment_sha256`，对 GitHub 返回的评论正文 UTF-8 字节计算 SHA-256。结构化评论以独立一行 `<!-- or-decision -->` 开头，后接一个 JSON 代码块；字段为 opportunity_id、action、run_id、reason、recovery_condition、new_task_id、project_url、new_task。所有可选值都显式使用 null。continue 时 new_task 必须是符合任务 Schema 的新任务对象，且 ID 与 new_task_id 一致；其他 action 的 new_task 必须为 null。评论 actor、最新正文及评论所属 Issue 由 GitHub API 获取并校验；`decided_at` 对应评论最新更新时间。评论修改会改变 hash，并产生新的提案，不得替换已经合并的决定。被接受的人工账号由仓库变量显式配置，未配置时拒绝生成或验证决定。

## 输入任务

必填字段为 schema_version、task_id、opportunity_id、question、hypothesis、success_criteria、falsification_criteria、deliverables、context_refs、budget、allowed_actions、stop_conditions、created_at。

- question 必须能通过实践回答；criteria 允许定性标准，但必须可核验。
- context_refs 指向具体版本的研究、Judge、历史结果和人类决定。消费者同时核对当前 main 上是否已有暂停/关闭/替代决定。
- budget 包含最大时长、允许费用与币种；未知预算须明确表示待人补充，不能推断无限额度。
- allowed_actions 明确允许的操作，涉及外部行动按原项目规则授权。
- 合并 PR URL、SHA、merged_by 从 GitHub 事实解析，不能信任 Agent 自填 approved=true。
- 已批准任务的实质修改再次走 PR；已领取时绑定 task 内容 hash。任务内容改变后旧运行停止并等待重新授权，不把最新上下文悄悄套入旧实验。
- 已有合并结果的任务视为完成，不再修改；下一轮验证使用新任务 ID，以保留原结果与输入 hash 的对应关系。

## 发现、领取、恢复

1. 定时同步 main，枚举有效 inbox，核对机会决定、已完成结果、开放结果 PR 与任务内容 hash。
2. 每个 task_id 对应一个任务 Issue，由中心端幂等创建并保存映射；重复触发复用既有 Issue。
3. 消费者在 Issue 提交结构化 claim 请求，含 task_id、task_hash、run_id、agent_id、请求时间。中心 Actions 串行处理领取请求，查询已有租约后发出确认回执。消费者等确认后才执行。
4. 不能用普通 assignee 或最后一条评论当原子锁。每任务 concurrency 串行化后，必须重新读取有效回执；处理触发采用重扫未处理请求，避免 Actions 合并排队事件导致漏领。
5. 初版默认租约 2 小时、每 30 分钟心跳；这是实现默认值，消费者可在任务预算范围内续租。过期显示待恢复，不能立即自动重复可能已有外部副作用的实验。
6. 中断后先按 run_id 查询结果与副作用日志，再恢复或请求人工处理。若外部消费者不能完成此握手，首次只做协议演练，运行状态保持未接通。
7. 暂缓/关闭即时由当前有效人类决定阻止新领取。运行中消费者在每次外部行动前及心跳时检查停止条件。

运行回执字段为 event_id、task_id、run_id、agent_id、task_hash、event_type（claim/accepted/heartbeat/blocked/resume/resumed/released/rejected）、timestamp、lease_until、reason；accepted 由中心确认。请求与确认区分，中心只接受配置的消费者身份。以事件 ID 去重，重跑不得发重复确认。

中心使用单个全局串行的 GitHub Actions 工作流处理所有任务 Issue；每次运行重新枚举并重扫所有未处理评论，定时和手动运行也执行同样的补扫。请求评论以 `<!-- or-request -->` 和 JSON 代码块表示，中心回执以 `<!-- or-receipt -->` 和 JSON 代码块表示，并带请求评论 ID。请求只有来自 `WORKFLOW_CONSUMER_LOGIN` 配置的账号才可被处理；回执只信任 GitHub Actions bot 实际发表的评论。中心使用处理时的服务端时间计算租约，不信任请求自填时间。未知预算、暂停/关闭决定、已有结果或失效任务 hash 时不得确认领取。

领取请求以 GitHub 评论创建时间计算，两小时内未处理则拒绝并要求重新提交，防止恢复运行时意外执行过期请求。租约续期不超过任务的总时长预算；费用预算或币种未知时不得确认领取。手动恢复只释放过期租约，后续仍需新的领取请求。

过期租约或任务哈希变化显示待恢复，不能因过期或任务重新批准而自动重新领取。人在检查运行及副作用后，可由 `WORKFLOW_HUMAN_LOGIN` 配置的账号发表 `<!-- or-recover -->` 结构化评论，明确 task_id、run_id 和处理理由；中心记录释放回执后才允许新领取。这一操作不代替对外部副作用的检查。Issue 创建与回执写入均先重扫 GitHub 事实，按任务标记与请求评论 ID 去重；同任务存在多个中心 Issue 时停止处理并报告，不猜测采用哪一个。使用同一个 GitHub 身份的人与消费者仍无法靠身份单独区分，须披露此限制。

## 输出结果与 PR

result.json 必填 schema_version、task_id、opportunity_id、run_id、task_hash、input_commit、started_at、finished_at、outcome、criteria_results、evidence_refs、actual_cost、remaining_unknown、recommendation。

outcome 为 supported/refuted/inconclusive/blocked；这是实验结论，立项由人决定。criteria_results 逐项对照输入标准；actual_cost 保存真实时长和费用，未知为 null。report.md 记录方法、实际操作、原始数据位置、反证、失败和可复现步骤。证据含采集时间、来源及内容摘要，有文件时附 hash。

PR 类型明确为 practice-result，关联任务 Issue 与输入合并 PR。同 task_id/run_id 重试更新已有分支和 PR。检查 main 是否已有该结果，避免重复归档。结果 PR 不允许擅自改任务预算、授权、人类决定或执行配置；需变更时另起明确提案。

结果 PR 合并后任务从已接受结果推导为完成，保留 inbox 原记录用于追溯；消费者跳过。结果 PR 关闭未合并时保留当前运行与原因，可补充后再提；不能直接当已完成。

## 提交与通知

评审 PR 与结果 PR 均关联机会 ID、任务 ID、证据版本，正文包含业务摘要、主要数据、关键未知和本次需人决定的事项。通过 GitHub reviewer/订阅机制通知人；个人账号共用提交身份时须实测通知行为，不能把创建 PR 成功等同于人收到通知。

Judge 的平台定时能力、GitHub 写入能力和实际授权必须分别验收。平台不能直接发 PR 时先保存完整提交包并明确失败，由已授权的 gh 执行端接力；不能把手工接力登记成自动交接。
