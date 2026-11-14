# Opportunity Runtime 项目指南

## 1. 项目定位

Opportunity Runtime 用来持续观察“钱的变化”，经过 Research 和 Judge，把大量外部变化压缩成少量值得人关注的机会。

固定链路：

```text
Sensing
→ Signal
→ Research
→ Opportunity Hypothesis
→ Judge
→ Human Decision
```

当前目标：

- 找到 1 个可持续经营的小现金流
- 建成 2–3 个可回测 / 可执行交易策略
- 每季度验证至少 1 个结构性摩擦机会

当前赚钱方式偏好：

```text
数据 / 情报服务
>
自动化运营
>
交易
>
完整产品
```

明确排除：

- 大团队
- 重资产
- 重线下
- 高库存
- 高客服 / 高售后

最终决策权始终在人。

---

# 2. 已确认的核心设计

系统只保留 5 个角色：

```text
Business Sensor
Friction Sensor
Market Sensor
Researcher
Judge
```

不要新增通用 Planner、Orchestrator、Supervisor、Multi-Agent Router 等角色，除非后续出现明确需求。

详细职责以项目内以下文档为准：

```text
docs/00-overview.md
docs/01-business-money-sensor.md
docs/02-friction-sensor.md
docs/03-market-sensor.md
docs/04-researcher.md
docs/05-judge.md
```

这些文档属于业务规则 Source of Truth。

---

# 3. 三个 Sensor

## 3.1 Business Money Sensor

执行平台：

**Gemini Scheduled Task**

关注四类变化：

```text
Budget Migration
New Toll Booth
Cost Curve Shift
Harvest Market
```

它回答：

> 哪里正在形成新的可持续利润池？

只输出 Signal。

禁止直接输出：

- 产品方案
- MVP
- 创业建议
- TAM
- 商业计划

输出位置：

```text
Google Drive/
Opportunity Runtime/
Signals/
Business/
```

---

## 3.2 Friction Sensor

执行平台：

**Grok Automation**

主要利用：

- X
- Web
- Reddit / community
- 用户反馈
- developer discussion

重点寻找：

```text
already paying
+
still doing manually
```

以及能够明确关联：

- revenue loss
- conversion loss
- labor cost
- support cost
- transaction failure

的摩擦。

它回答：

> 哪里已有的钱因为摩擦没有顺利流动？

输出位置：

```text
Google Drive/
Opportunity Runtime/
Signals/
Friction/
```

---

## 3.3 Market Sensor

执行平台：

**GitHub Actions + Python + Tushare Pro**

负责：

```text
fetch
calculate
filter
detect anomaly
```

重点观察：

- price
- volume
- flow
- spread
- carry
- volatility
- relative value
- valuation
- regime change

原则：

> 能确定性计算的事情不要交给 LLM。

LLM 不负责凭感觉扫描市场。

输出位置：

```text
Google Drive/
Opportunity Runtime/
Signals/
Market/
```

如果 V1 上传 Drive 增加明显复杂度，可以暂时将 Market Signal 输出到 Git Repo，再由 Researcher 读取。

不要为了统一存储额外建设后端。

---

# 4. Researcher

执行平台：

**Gemini Scheduled Task**

输入：

```text
Signals/Business/
Signals/Friction/
Signals/Market/
```

Researcher 不负责继续扫描世界，只研究已有 Signal。

核心四个 Gate：

```text
Money
Mechanism
Persistence
Capture
```

具体含义：

1. Money：到底是哪笔真实的钱？
2. Mechanism：为什么会产生利润 / 错价 / 可回收价值？
3. Persistence：为什么不会很快消失？
4. Capture：为什么用户有机会捕获其中的价值？

只有通过这四个 Gate，Signal 才可以升级成 Opportunity Hypothesis。

Researcher 合法输出状态：

```text
KILL
WATCH
HYPOTHESIS_READY
BLOCKED
```

Research 的目标不是“研究得尽量全面”，而是：

> 研究到足以改变下一步决策。

输出：

```text
Google Drive/
Opportunity Runtime/
Research/
```

---

# 5. Judge

执行平台：

**GPT**

频率：

**每 3 天一次（Asia/Taipei 19:00；每轮回看近 7 天 Research 并跨轮去重）。**

输入：

```text
Research/
```

Judge 不对所有机会做统一百分制评分。

Judge 的职责是：

> 决定下一单位人类注意力应该花在哪里。

输出四类：

```text
NOW
NEXT
WATCH
DROP
```

默认关注顺序：

```text
Cashflow Business
>
Trading Strategy
>
Friction Opportunity
```

时间敏感且证据成熟的机会允许插队。

Judge 输出位置：

```text
Google Drive/
Opportunity Runtime/
Judge/
```

如果 GPT Scheduled Task 无法稳定读取 Google Drive，不要为了它开发中继系统。

退化方案：

> 每周由用户手动触发 GPT Judge。

---

# 6. Signal 协议

所有 Sensor 输出应尽量使用统一结构：

```text
Signal ID

Type
Business / Friction / Market

What Changed
发生了什么变化？

Money
涉及哪笔真实资金、收入、成本或资产？

Evidence
2–4 条最重要原始证据。

Mechanism
为什么该变化可能具有经济意义？

Persistence
Temporary / Emerging / Persistent

Next Question
最值得继续调查的问题。

Task Version
生成该 Signal 的任务版本。

Generated At
生成时间。
```

Signal 不是 Opportunity。

禁止：

```text
Signal
→ 直接 Build
```

必须：

```text
Signal
→ Research
→ Opportunity Hypothesis
```

---

# 7. Opportunity Hypothesis 协议

Researcher 通过四个 Gate 后才允许生成：

```text
Opportunity Hypothesis

Money
哪笔钱？

Mechanism
价值为什么产生？

Capture
可能捕获哪个节点？

Durability
为什么不会快速消失？

Evidence
最强证据。

Counter Evidence
最重要反证。

Critical Unknown
当前最可能改变 Decision 的未知变量。

Falsification
什么情况出现时应该推翻？

Next Test
下一步最低成本验证。
```

---

# 8. Research Stop Protocol

Research 满足任一条件即停止：

1. 已有足够强反证，可以 KILL
2. 四个 Gate 已经足够回答
3. 剩余关键未知只能通过真实实验 / 私有数据解决
4. 继续搜索公开资料不太可能改变结论

禁止无限 Research。

---

# 9. Google Drive 协议

V1 使用 Google Drive / Docs 作为 Agent 之间的共享工作层。

固定逻辑结构：

```text
Opportunity Runtime/
  Signals/
    Business/
    Friction/
    Market/
  Research/
  Judge/
```

Drive 是：

> Agent 与人共享结果的工作区。

V1 不引入：

- 数据库
- Queue
- Event Bus
- 自建状态服务

除非后续真实运行暴露需求。

---

# 10. 已确认的平台分工

当前默认方案：

```text
Gemini
├─ Business Sensor
└─ Researcher

Grok
└─ Friction Sensor

GitHub Actions
└─ Market Sensor

GPT
└─ Judge
```

这是 V1 默认方案。

Codex 不要主动重新设计平台分工。

如果发现某个平台能力确实无法满足要求：

1. 记录限制
2. 给出最小替代方案
3. 不立即迁移整个架构

---

# 11. 当前可用资源

订阅：

```text
ChatGPT Plus
Google AI Pro
X Premium / Grok
```

计算资源：

```text
GitHub Actions
Cloudflare
Google Cloud
Mac mini M4 7×24
```

API：

```text
Tushare Pro
Tavily
Firecrawl
```

其他：

```text
家庭公网 IP
```

默认优先级：

```text
现成 Scheduled Task
>
简单脚本 / GitHub Actions
>
Cloudflare Worker
>
Mac mini 长驻 Agent
>
自建 Runtime
```

不要因为资源已经存在就强行使用。

---

# 12. Tavily / Firecrawl 的定位

当前不作为独立 Sensor。

只作为后续需要时的 Research / Sensing 工具。

默认定位：

```text
Tavily
→ discovery / search

Firecrawl
→ fetch / extract
```

只有 Gemini / Grok 原生搜索能力不足时再接入。

---

# 13. Pi Agent + Mac mini

Pi Agent 不是 V1 必需依赖。

只有出现以下需求才升级：

- Scheduled Task 无法可靠完成复杂 Research
- 需要同时调用 Tavily / Firecrawl / Python / Browser
- 需要本地长期状态
- 需要事件驱动
- 需要复杂回测 / 本地数据
- 需要统一 Agent Skills
- 需要 7×24 本地 Worker

届时推荐：

```text
Pi Agent
+
Mac mini M4
```

作为 Agent Worker。

它应替代某个现有执行角色，而不是重新发明整套 Runtime。

---

# 14. V1 项目结构

固定采用以下结构：

```text
opportunity-runtime/
├── README.md
├── AGENTS.md
├── CHANGELOG.md
│
├── docs/
│   ├── 00-overview.md
│   ├── 01-business-money-sensor.md
│   ├── 02-friction-sensor.md
│   ├── 03-market-sensor.md
│   ├── 04-researcher.md
│   └── 05-judge.md
│
├── tasks/
│   ├── gemini/
│   │   ├── business-sensor.md
│   │   └── researcher.md
│   │
│   ├── grok/
│   │   └── friction-sensor.md
│   │
│   ├── gpt/
│   │   └── judge.md
│   │
│   └── github-actions/
│       ├── market-sensor.md
│       └── market-sensor.yml
│
├── schemas/
│   ├── signal.md
│   └── opportunity-hypothesis.md
│
└── scripts/
    └── market/
```

暂时不要增加：

```text
backend/
server/
database/
queue/
orchestrator/
dashboard/
mcp/
```

---

# 15. tasks/ 的协议

`docs/`：

> 说明角色为什么存在、遵循什么业务规则。

`tasks/`：

> 各平台可以直接使用的实际任务配置和 Prompt。

例如：

```text
docs/01-business-money-sensor.md
```

是 Source of Truth。

而：

```text
tasks/gemini/business-sensor.md
```

是根据角色规则生成的 Gemini 可用 Prompt。

如果角色规则改变：

1. 先修改 docs
2. 再更新 tasks
3. 记录 CHANGELOG

不要只偷偷改 Prompt。

---

# 16. Prompt 版本协议

每个实际任务文件必须有简单 metadata：

```yaml
task_id: business-sensor
version: 0.1.0
platform: gemini
role_spec: docs/01-business-money-sensor.md
updated_at: YYYY-MM-DD
```

不要建设复杂 Prompt Registry。

Git 是唯一版本历史。

---

# 17. CHANGELOG 协议

只记录会改变 Runtime 行为的变化，例如：

```text
## 0.2.0

Changed
- Business Sensor 从每日最多 5 个 Signal 降为 3 个
- Researcher 增加 Counter Evidence 要求

Reason
- 前两周 Signal 噪声过高
```

不记录普通格式调整。

---

# 18. AGENTS.md

在项目根目录创建 `AGENTS.md`。

内容至少包括以下规则：

```text
# Opportunity Runtime Agent Rules

## Mission

Maintain the simplest working Opportunity Runtime.

Do not redesign the architecture unless evidence from actual operation requires it.

## Source of Truth

Business rules live in:

docs/

Platform task prompts live in:

tasks/

If behavior changes, update the relevant role spec first, then the generated/platform task.

## Architecture

V1 fixed roles:

- Business Sensor → Gemini
- Friction Sensor → Grok
- Market Sensor → GitHub Actions
- Researcher → Gemini
- Judge → GPT

Do not introduce additional agent roles without a concrete requirement.

## Simplicity

Prefer:

existing scheduled tasks
> small scripts
> GitHub Actions
> Cloudflare Workers
> long-running custom agents

Do not introduce databases, queues, orchestration systems, dashboards, MCP servers, or custom runtimes unless an observed limitation requires them.

## Deterministic Work

Use code for deterministic tasks such as:

- fetching
- calculations
- filtering
- deduplication
- backtests

Use LLMs for:

- research
- interpretation
- falsification
- judgment

## Human Control

Agents may sense, research, and judge.

Agents must not autonomously:

- deploy capital
- execute trades
- launch paid products
- commit irreversible external actions

without explicit user approval.

## Change Discipline

Every behavioral change must be traceable through Git.

For meaningful changes:

1. update the relevant spec
2. update affected task prompts/config
3. update CHANGELOG.md
4. keep changes minimal

Do not improve unrelated parts of the project.

## Uncertainty

Do not guess platform capabilities.

If Gemini, Grok, GPT, Google Drive, GitHub Actions, or another external platform capability is uncertain, mark it as a validation item or TODO.

Do not add infrastructure purely to work around an unverified limitation.
```

保持 AGENTS.md 短、硬、稳定。

不要把所有业务细节复制进去。

---

# 19. 第一阶段交付

Codex 当前只需要完成：

### A. Project skeleton

建立上述 V1 目录。

### B. Import docs

放入现有 6 份已经确认的设计文档。

### C. AGENTS.md

按照本指南生成根级项目约束。

### D. Platform tasks

生成：

```text
tasks/gemini/business-sensor.md
tasks/gemini/researcher.md
tasks/grok/friction-sensor.md
tasks/gpt/judge.md
tasks/github-actions/market-sensor.md
```

Prompt 必须严格继承对应 Role Spec。

### E. Market Sensor skeleton

只创建最小 GitHub Action / Python 结构。

不要一开始实现完整交易策略。

### F. Versioning

建立：

```text
CHANGELOG.md
```

所有 Task 添加版本 metadata。

---

# 20. 当前不做

V1 明确不做：

- 自动创建 Gemini/Grok/GPT Scheduled Task 的平台 API
- 自建 Agent Scheduler
- Cloudflare control plane
- 数据库
- Queue
- Dashboard
- Opportunity management Web UI
- Pi Agent runtime
- Mac mini daemon
- MCP server
- 自动交易
- 自动产品发布

如果后续需要，再基于真实运行问题升级。

---

# 21. Codex 执行原则

这不是一个架构探索任务。

已经确认的设计应直接实现。

Codex 应：

```text
read
→ structure
→ generate
→ validate consistency
→ report
```

而不是：

```text
read
→ redesign
→ propose many alternatives
```

如果发现方案内部存在明确冲突：

> 标记冲突并采用最小修改解决。

如果只是存在“理论上更好的设计”：

> 不修改。
```

---

# 22. V1 成功标准

第一阶段完成后，应可以做到：

1. 打开 `tasks/` 就能复制 Prompt 创建 Gemini / Grok / GPT 任务
2. Market Sensor 有可运行的最小 GitHub Actions 骨架
3. 所有 Prompt 能追溯到对应 Role Spec
4. 后续任何行为调整可以通过 Git / CHANGELOG 追踪
5. 不依赖额外自建 Runtime 基础设施

目标是：

> **先让现成 Agent 产品组成 Opportunity Runtime，再根据真实使用结果决定是否需要自建 Agent Worker。**


---

# 19. Judge 数据镜像与只读决策看板（2026-11-14）

Judge 在 Google Drive 原目录归档并验证后，将 Research 与 Judge Google Docs 正文同步至私有仓库 `or-archive/research/` 和 `or-archive/judge/`；公开 GitHub Pages 只能部署 `site/` 脱敏投影，完整资料绝不可放入站点 artifact。镜像对账存储在 `or-archive/manifest.json`。新频次每 3 天；每自然周最多主动推进 1 个新 Opportunity 不变。历史文档未回填完毕前，必须报告 backfill_pending。完整边界见 `or-archive/README.md`。
