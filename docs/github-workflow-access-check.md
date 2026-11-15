# GitHub 接入核查

2026-11-15，使用本机 gh 核查 `zhiweiofli/opportunity-runtime-market-sensor`：

- 私有仓库，默认分支 `main`；重新 fetch 后为 `c7aebc9cd70615e8a2234933ae9f7689e785bf81`。
- 当前身份对仓库有 admin、maintain、push、pull、triage 权限。
- 仓库 API 返回 `has_pages: false`；Pages API 返回 404。运行 43575263389 在 `actions/configure-pages` 查询站点时返回 404，因此没有成功部署的证据。
- rulesets API 返回 403，提示升级 GitHub Pro 或公开仓库；不能据此推断没有规则。
- 开放 PR #2 是既有 Market 工作，不作为本次实施基线；核查时无开放 Issue。
- Actions 默认 token 权限为 read；仓库的 `can_approve_pull_request_reviews` 为 false。GitHub 将此设置用于控制 Actions 是否可以创建或批准 PR，因此当前以 `GITHUB_TOKEN` 自动创建决定 PR 的环节不能按预期接通。该设置同时涉及批准权限，不在本次核查中修改。参见 [GitHub Actions 仓库设置](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)。
- 2026-11-15 初查未发现以 `WORKFLOW_` 开头的仓库 Actions 变量；随后已将 `WORKFLOW_HUMAN_LOGIN` 配置为已核验的仓库所有者 `zhiweiofli` 并回读确认。消费者账号和公开投影授权仍未配置；人和 Agent 若共用身份，无法仅靠 GitHub 身份证明人工操作。订阅 API 返回 404，不能据此断言通知已开启或关闭。

平台能力、通知、Pages 可用性与发布范围仍需独立验收。此核查不表示机会闭环已经实现。
