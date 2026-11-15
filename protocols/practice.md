# 实践 Agent 接入

本协议使用 [实践契约](../docs/practice-agent-contract.md) 和 `schemas/workflow/` 的 JSON Schema。代码与看板仍在实施中；未收到中心端确认的领取请求不能执行。

- 定时读取可信 main 的 `practice/inbox/<task_id>/task.json`，核对同机会最新决定、已合并结果及开放结果 PR。
- 对任务文件的原始 UTF-8 字节计算 SHA-256，不规范化 JSON。记录读取的 main commit 与 hash；任务改变时停止旧运行。
- 引用 `{ "path": "...", "commit": "<完整 40 位 SHA>" }` 指向 main 历史中的普通文件。相对路径不可越过仓库。来源缺口填 null 并说明，不编造。
- 输入预算的 `max_duration` 用小时、`max_cost` 用 `currency` 指明的币种；未知为 null，不代表无限。`allowed_actions` 和停止条件不构成未列出的授权。
- 判断标准使用 `{ "id": "...", "description": "..." }`；结果的 `criteria_results` 使用相同 ID，逐项提供 `result`。
- 输出 `practice/results/<task_id>/<run_id>/result.json` 和同目录非空 `report.md`。`evidence_refs` 至少一项；引用文件时提供其 SHA-256。结果 PR 须关联任务 Issue 和输入 PR；实际合并证据从 GitHub 读取。
- PR 正文包含唯一类型标记，例如 `<!-- workflow-type: practice-result -->`。实际变更与类别会分别检查。创建 PR 或获得自动检查通过不等于人已验收。
- 领取、心跳、阻塞、恢复以任务 Issue 的结构化评论交互，消费者等待 Actions bot 的对应确认后才执行；外部消费者与生产定时仍需单独验收。

请求正文必须只含标记和 JSON 代码块，字段都必填；`event_type` 为 `claim`、`heartbeat`、`blocked`、`resume` 或 `released`。`blocked` 和 `resume` 必须说明原因。`event_id` 在所有请求中唯一，重试使用同一条评论而非新建事件；`reason` 可为 null。

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

中心的消费者和人工 GitHub 登录名分别配置在仓库变量 `WORKFLOW_CONSUMER_LOGIN`、`WORKFLOW_HUMAN_LOGIN`。变量未配置时对应操作不被接受。若两者共用身份，GitHub 无法独立证明决定由人而非消费者发起；须使用人工合并约定，强制身份隔离则需要单独的 bot 账号。

本地检查（只检查数据，GitHub 合并和身份由在线检查另行验证）：

```sh
python3 -m pip install -r requirements-workflow.txt
python3 scripts/workflow/validate.py --root . --base <可信主分支提交SHA>
python3 scripts/workflow/check_paths.py --type practice-result --base <base> --head <head>
python3 -m unittest discover -s scripts/workflow -v
python3 scripts/workflow/synthetic_demo.py
```

最后一条仅在本地模拟领取竞争、心跳和过期恢复，输出明确标记 synthetic，**不连接 GitHub**；它不能证明实际消费者、通知或平台定时已接通。
