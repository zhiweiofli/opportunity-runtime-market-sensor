---
handoff_id: market-cloud-v1
revision: 1
kind: development-handoff
repository: zhiweiofli/opportunity-runtime-market-sensor
base_branch: main
market_task_version: 0.2.0
environment_id: ccarenv_b64_Y2NhcmVudl9iZGYzYmMyMmVkMWM4MTkxOTU1MDRiYWNjOGJlZjk2Yg
submission_status: not-created
updated_at: 2026-10-20
---

# Market V1 云端开发交接

这是 Codex 开发任务的交接材料，不是新增业务角色。用户已表示完成云端环境初始化并授权启动任务，随后提供 Environment ID；本会话 CLI 选择器未列出目标环境，使用该 ID 和 main 分支直接提交后返回 `environment not found`、退出 1，未创建任务。Chrome 界面访问未获批准，桌面应用的界面控制被系统安全限制拦截。**材料准备不代表任务已提交。** 最新实际提交/运行状态另记于 [验证记录](validation.md)。

以下任务使用云端检出的仓库文件，不依赖本机路径或本聊天历史。可通过官方 CLI 指定核实后的 Environment ID 和 main 分支提交；若 CLI 无法访问该环境，也可在此仓库对应的云端任务中直接粘贴全文。不要借用其他仓库环境。

```text
在 zhiweiofli/opportunity-runtime-market-sensor 的 main 分支基线上完成 Market Sensor V1 云端开发与验收。本任务先复现已有管线、修复实际发现的缺陷、补齐云端执行证据；正式策略规则尚未由用户提供，不自行猜定市场范围、标的池、历史基准、阈值和定时频率。

先读 AGENTS.md、PROJECT_GUIDE.md、docs/README.md、六份 docs/00-overview.md 至 docs/05-judge.md、docs/deployment.md、docs/validation.md、docs/source-import.json，再检查 tasks/github-actions/、schemas/、scripts/market/ 及 .github/workflows/。以现有材料为基础，不重新设计架构。确认实际仓库和基线 commit；仓库不符则停止并说明，不在其他项目工作。

已有交付：Market Python/task 为 0.2.0，标准库实现；Market CI 对 push/PR 做离线验证，Market Sensor 用 workflow_dispatch 支持 fixture 或 Tushare daily，输出 artifact。GitHub CI、手动 fixture 与一次真实 HTTPS daily 接入已通过，具体 run/错误历史见 docs/validation.md。这些不替代本次云端验证，也不需要重建仓库或重复部署同一 workflow。

实际执行并记录：
1. python3 -m unittest discover -s scripts/market -p 'test_*.py' -v
2. python3 scripts/market/market_sensor.py --source fixture --demo-abs-pct 5
3. 用代码读取 outputs/market/report.json，核对 status=SIGNALS、3 observations、2 signals、task_version=0.2.0、demo_only=true、research_eligible=false。
4. 核对生效 workflow 和 tasks/ 副本一致、只读权限、手动输入、Secret 映射及错误报告 artifact。检查已有测试覆盖的契约；只为实际缺陷增加必要测试，不重复编写镜像测试。

若发现可复现缺陷，以最小改动修复并运行相关验证。涉及业务行为或输出契约时，先补 docs/ 中约定，再改 task/code、必要版本与 CHANGELOG；六份导入原稿和 PROJECT_GUIDE 原文保留。只有云端验证/手册补充时不提升 Market 业务版本。没有缺陷时保持代码，补齐 docs/validation.md 的本次云端证据即可。

固定边界：行情计算只用确定性 Python；所有当前结果仍为演示，不作为真实机会交 Researcher。不新增角色、数据库、队列、调度服务、MCP、统一 Runtime、交易、自动资金动作或 Drive 上传服务。时区沿用 Asia/Taipei；未确定正式规则前不新增行情 schedule。

开发与离线验收不需要 TUSHARE_TOKEN。不要索取、读取、复制或输出 token，不将 GitHub Secret 传到云端任务；真实 API 验证沿用 GitHub Actions 已有证据，新增接入需求另明确。平台网络或工具不可用时记录实际阻塞，不把没跑的测试签为通过。

交付：给出修改文件与必要原因、实际命令/退出码/结果、云端基线 commit、正式规则待填项，以及可审查的补丁。原始临时输出不提交 Git，只把脱敏证据摘要写入 docs/validation.md。不要直接推 main、合并或重建已部署资源；如提供 PR，返回真实 URL。完成标准是本次云端验证有事实证据，必要修复通过检查，变更可供复核；不能将这签成正式交易策略或定时已验收。
```

官方提交参数依据：[Codex CLI cloud 参考](https://learn.chatgpt.com/docs/cli/reference#codex-cloud)。此处不保存凭据，也不猜测环境 ID。取得 ID 后先核对目标；提交成功必须记录真实任务 URL/ID，随后读取状态，区分已提交、运行中与完成。
