# Opportunity Runtime Agent Rules

## Mission
Maintain the simplest working Opportunity Runtime. Do not redesign it without evidence from actual operation.

## Source of Truth
Business rules belong in `docs/`; platform prompts/config belong in `tasks/`.
The six original business documents are in `docs/00-overview.md` through `docs/05-judge.md`; preserve imported originals. `PROJECT_GUIDE.md` fixes V1 implementation scope and platform assignments. Record any reconciliation in `docs/README.md`; role review does not imply platform/runtime acceptance.
For behavior changes: update the relevant spec first, affected tasks/code second, and `CHANGELOG.md`; trace changes through Git.

## Architecture
Fixed roles: Business Sensor → Gemini; Friction Sensor → Grok; Market Sensor → GitHub Actions + Python + Tushare Pro; Researcher → Gemini; Judge → GPT (every 3 days in Asia/Taipei; manual fallback).
No additional roles without a concrete requirement.
Prefer existing scheduled tasks > small scripts / GitHub Actions > Cloudflare Workers > long-running agents.
No database, queue, orchestration system, MCP server, custom runtime, or platform deployment API without an observed need. A static read-only Judge Pages dashboard is explicitly requested; avoid growing it into a backend.

## Deterministic Work and Human Control
Use code for fetching, calculations, filtering, deduplication and backtests; use LLMs for research, interpretation, falsification and judgment.
Agents may sense, research and judge. Capital deployment, trades, paid product launches and irreversible external actions require explicit human authorization. V1 implements no trading.

## Decision Discipline
Do not guess silently. Resolve material uncertainty from repository evidence first; use the simplest supported interpretation.
Proceed with safe, reversible assumptions. Ask only for ambiguity affecting architecture, contracts, compatibility, safety or irreversible decisions.
Unverified platform capabilities are TODO/validation items, never reasons to add speculative infrastructure.

## Scope and Simplicity
Implement the smallest coherent change. Every changed line must serve the request or a necessary integration, compatibility, migration, cleanup or verification consequence.
Avoid speculative features, premature abstractions, unnecessary configuration and defenses already guaranteed by invariants. Prefer conceptual simplicity. Mention unrelated issues without fixing them.

## Efficient Execution
Optimize useful progress per cycle. Batch independent reads and checks; retrieve targeted evidence and reuse it. Keep plans internal unless a consequential decision needs explanation.
Use subagents only when substantial work justifies their separate context and setup cost, and delegation is authorized.

## Verification
For non-trivial work, identify observable success criteria. Follow Understand → Change → Verify → Inspect Diff.
Use the smallest relevant tests/checks; expand only when evidence shows failure or uncertainty.

## PWR Sync
Use the global `pwr-sync` skill for durable project-state changes, meaningful long-term decisions or explicit sync requests.
Let the current PWR Policy decide persistence; never guess project/space IDs. Do not sync routine implementation, debugging, commands, brainstorming or temporary context.
