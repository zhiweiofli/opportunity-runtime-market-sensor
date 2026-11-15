# 实践 Agent 接入

本协议使用 [实践契约](../docs/practice-agent-contract.md) 和 `schemas/workflow/` 的 JSON Schema。代码与看板仍在实施中；未收到中心端确认的领取请求不能执行。

- 定时读取可信 main 的 `practice/inbox/<task_id>/task.json`，核对同机会最新决定、已合并结果及开放结果 PR。
- 对任务文件的原始 UTF-8 字节计算 SHA-256，不规范化 JSON。记录读取的 main commit 与 hash；任务改变时停止旧运行。
- 引用 `{ "path": "...", "commit": "<完整 40 位 SHA>" }` 指向 main 历史中的普通文件。相对路径不可越过仓库。来源缺口填 null 并说明，不编造。
- 输入预算的 `max_duration` 用小时、`max_cost` 用 `currency` 指明的币种；未知为 null，不代表无限。`allowed_actions` 和停止条件不构成未列出的授权。
- 判断标准使用 `{ "id": "...", "description": "..." }`；结果的 `criteria_results` 使用相同 ID，逐项提供 `result`。
- 输出 `practice/results/<task_id>/<run_id>/result.json` 和同目录非空 `report.md`。`execution_intervals` 列出实际执行的每一段开始和结束时间，停机或等待恢复的间隔不得计作执行；每段必须有中心确认的有效租约覆盖。`evidence_refs` 至少一项；随结果提交的文件放在该运行的 `evidence/` 下，引用的 commit 填 null 并提供 SHA-256；引用既有文件则提供固定 commit。结果 PR 须关联任务 Issue 和输入 PR；实际合并证据从 GitHub 读取。
- PR 正文包含唯一类型标记，例如 `<!-- workflow-type: practice-result -->`。实际变更与类别会分别检查。创建 PR 或获得自动检查通过不等于人已验收。
- 领取、心跳、阻塞、恢复以任务 Issue 的结构化评论交互，消费者等待 Actions bot 的对应确认后才执行；外部消费者与生产定时仍需单独验收。

请求正文必须只含标记和 JSON 代码块，字段都必填；`event_type` 为 `claim`、`heartbeat`、`blocked`、`resume` 或 `released`。`blocked` 和 `resume` 必须说明原因。`event_id` 在所有请求中唯一；等待回执时复查同一条评论，收到 rejected 后如需重新申请则使用新的 event_id 和新评论；`reason` 可为 null。

````text
<!-- or-request -->
```json
{"event_id":"event-1","task_id":"task-1","run_id":"run-1","agent_id":"consumer-1","task_hash":"<64位SHA-256>","event_type":"claim","timestamp":"2026-01-01T00:00:00Z","reason":null}
```
````

中心回执带 `request_comment_id`，类型为 accepted、heartbeat、blocked、resumed、released 或 rejected。只有来自 GitHub Actions bot 且绑定原评论的 `accepted` 或续租 `heartbeat` 回执有效。阻塞期间可心跳但不会自动恢复，解决阻塞后用 `resume` 请求。消费者检查租约时间和 hash，并在每次外部行动前核对 main 与停止条件。请求中的 timestamp 是记录信息，租约以中心处理时间计算。

租约过期或任务哈希变化后，须由配置的人类账号确认已检查副作用，再发恢复评论；恢复不会自动执行任何实验。

````text
<!-- or-recover -->
```json
{"task_id":"task-1","run_id":"run-1","reason":"已核查该运行的结果与外部副作用"}
```
````

人类决定评论使用下列格式。`launch` 须引用已合并结果；`pause` 必须写恢复条件。继续验证时 `action` 设为 `continue`，填写新任务 ID，并在 `new_task` 中提供完整任务 JSON；其余动作的 `new_task_id` 和 `new_task` 为 null。中心只创建待审 PR，合并后决定才生效。

````text
<!-- or-decision -->
```json
{"opportunity_id":"opp-1","action":"pause","run_id":"run-1","reason":"证据不足","recovery_condition":"取得新证据","new_task_id":null,"project_url":null,"new_task":null}
```
````

当前仓库禁止 Actions 创建 PR。如果自动创建因权限失败，工作流日志会显示失败，已创建的 `codex/decision-d-...` 分支保留以便重试。人可核对该分支与原评论，再在 GitHub 手动建立指向 main 的 PR，在正文独立一行写入 `<!-- workflow-type: decision -->` 并链接原评论；等待可信校验通过后再决定是否合并。手动接力不算自动交接或通知验收；如没有留下分支，先排查日志，不猜测或跳过校验。

中心的真实消费者、合成测试消费者和人工 GitHub 登录名分别配置在仓库变量 `WORKFLOW_CONSUMER_LOGIN`、`WORKFLOW_SYNTHETIC_CONSUMER_LOGIN`、`WORKFLOW_HUMAN_LOGIN`。变量未配置时对应操作不被接受；真实与合成消费者同时配置时须使用不同账号。synthetic 任务只能执行 `synthetic-only` 动作：可在此私有仓库提交测试评论和 PR，但不得付费、联系外部人员或产生其他外部副作用；所有来源和上下文必须显式标识 synthetic，例如仓库中的 `examples/synthetic/research.md`。若人工与任一消费者共用身份，GitHub 无法独立证明决定由人而非程序发起；须使用人工合并及测试约定，强制身份隔离则需要单独的 bot 账号。

本地检查（只检查数据，GitHub 合并和身份由在线检查另行验证）：

```sh
python3 -m pip install -r requirements-workflow.txt
python3 scripts/workflow/validate.py --root . --base <可信主分支提交SHA>
python3 scripts/workflow/check_paths.py --type practice-result --base <base> --head <head>
python3 -m unittest discover -s scripts/workflow -v
python3 scripts/workflow/synthetic_demo.py
```

最后一条仅在本地模拟领取竞争、心跳和过期恢复，输出明确标记 synthetic，**不连接 GitHub**；它不能证明实际消费者、通知或平台定时已接通。

实施 PR 合并后，先刷新 `origin/main`，再从包含合成材料的当前 main 生成独立的测试评审包（`trial-1` 需换成未使用的唯一后缀；输出目录须不存在）：

```sh
python3 examples/synthetic/build_review.py --id trial-1 --input-commit "$(git rev-parse origin/main)" --output /tmp/or-synthetic-trial-1
```

检查生成的机会与任务后，将文件放到基于该 main SHA 的评审分支并建立带 review 类型标记的 PR。只有人在 GitHub 合并该测试 PR 后，中心才可创建任务 Issue；测试消费者的身份须单独配置。测试全程只处理合成材料和零费用动作，人工接力、测试消费者与真实项目各自标明，不能相互冒充。

任务 Issue 创建后，可以用本仓库提供的测试消费者发起领取；以下参数需换成实际测试 ID、Issue 编号和已配置的人类账号。它只对 synthetic 任务工作。首次调用创建一条测试领取评论，等待中心回执后再次运行相同命令；确认租约有效后才在新目录准备合成结果包，不会自动创建结果 PR。

```sh
python3 scripts/workflow/synthetic_consumer.py --repo zhiweiofli/opportunity-runtime-market-sensor --task-id synthetic-t-trial-1 --run-id synthetic-run-trial-1 --agent-id synthetic-consumer --issue 123 --output /tmp/or-synthetic-result-trial-1 --human zhiweiofli
```
