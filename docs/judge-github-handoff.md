# Judge GitHub 交接：待接通的提示词补充

**单独待办：用户要求延后线上 Judge 定时任务的核对与更新，后续单独处理。**本次继续 GitHub 闭环实现，不修改该任务，也不把提示词草稿当成已经接通。

现有仓库只记录 `judge@0.2.2` 的运行约定，未保存定时任务的完整当前提示词。根项目 `tasks/gpt/judge.md` 是较早的 `judge@0.2.1` 周频版本，不能当成当前任务的完整替代。Drive 搜索另找到 2026-10-17 的 [System Design & Task Prompts](https://docs.google.com/document/d/1UUjmgB8apFLh_SPA29n1SGbU3POGsn3hFDujsrpV6-w/edit)，但它早于当前运行约定，不能证明当前定时提示词。当前环境未获得桌面应用的操作权限，无法直接核对线上任务。以下是供后续核对和追加的草稿；尚未修改线上任务，也未验证定时轮次的 GitHub 写入能力。

## 拟追加的提示词

```text
在保持现有 Judge 判断规则和 Drive 保存要求的前提下，读取 GitHub 主分支上已接受的机会、实践结果和人类决定，并与本轮 Research 交叉核对。保留输入的版本、来源与缺口；读取不完整时明确报告，不把未知当作没有记录。演示数据和 PILOT 不能变成真实机会。

目标仓库是 zhiweiofli/opportunity-runtime-market-sensor，基线读取其当前 main 和完整 commit SHA。每 3 天 Asia/Taipei 19:00 回看最近 7 天并复核历史候选；每自然周最多主动推进一个新机会。读取 or-archive/manifest.json、关联 Research/Judge 镜像、opportunities/、practice/results/ 和各机会 decisions/；不能读取完整输入时注明覆盖缺口，不声称完成去重。Drive 仍是 Research 和 Judge 原文的权威来源。

对每个拟独立批准的机会，按仓库当前已实施的协议准备独立评审提案，包含机会记录、证据和明确的验证任务；WATCH 或 DROP 不创建实践任务。人合并评审 PR 后任务才获批准。结果合并表示接受记录，不代表人已决定立项。不得把模型建议写成人类决定，也不得擅自授权费用、外部联系、交易或其他需要人批准的行动。

读取 protocols/practice.md 和 schemas/workflow/ 中当前版本的 opportunity.schema.json、task.schema.json；必须按 Schema 构造有效 UTF-8 JSON，不能用说明文字代替文件。机会写入 opportunities/<opportunity_id>/opportunity.json；任务写入 practice/inbox/<task_id>/task.json。一个评审 PR 只对应一个机会，旧机会 ID 沿用，新任务 ID 全局唯一。success_criteria 与 falsification_criteria 的每项都有唯一 id 和 description；context_refs 使用仓库相对 path 和 main 历史中的完整 commit SHA。source_refs 保留 Drive Doc ID、来源更新时间、镜像路径和固定 commit；缺失字段为 null 并说明缺口。金额注明数值、currency、unit、basis 及证据；未知值为 null，不填零。预算以小时、币种和金额明确约束，未知预算不得解释为无限。public 字段只填经允许公开的脱敏内容，无法确定披露范围就省略。

评审 PR 正文必须单独包含 `<!-- workflow-type: review -->`，并写明业务摘要、机会和任务 ID、证据版本、主要数据、关键未知和需要人决定的事项。新分支以当前 main 为基线，PR 实际 diff 只包含本机会与相应任务、必要镜像；禁止修改校验器、工作流、其他机会或人类决定。提交前复核 Schema、路径、引用、演示排除及 diff。若已有评审或结果 PR，先核对其状态；不要把关闭的未合并提案当作已批准或已完成。任务内容更新也须重新经过评审合并。

如果本平台在实际运行中能访问 GitHub 并具备创建分支、写入文件和发起 PR 的授权，按仓库协议提交并核对回执，提供 PR 链接。否则输出包含完整文件内容、目标路径、基线 SHA 和 PR 正文的提交包，标记待人工接力；不得声称已创建 PR 或完成自动交接。Drive、GitHub 和通知分别报告实际结果。

成功创建 PR 不是通知送达的证据。若平台不能验证实际通知，明确写“通知未验证”。结果或决定未合并时不得写成已接受或已立项。保留每轮真实生成时间、输入版本、GitHub 同步状态及失败原因，不能以计划时间冒充实际发生时间。
```

## 接通与验收

1. 从实际定时平台读取当前完整提示词、时间和权限；保留原文与版本，确认上述补充与线上配置一致后再修改。
2. 协议、校验及 PR 路径落地后，将精确字段、路径和版本补入提示词；在普通轮次验证读取、提交及失败回执。
3. 检查至少一次无人值守定时运行是否实际创建分支、文件和 PR，并记录运行、PR 和通知证据。人工 `gh` 接力只证明人工路径。
4. 不把读取本文件或准备提交包当作平台已更新、通知已送达或定时自动化已验收。
