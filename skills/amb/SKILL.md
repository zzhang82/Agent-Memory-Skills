---
name: amb
description: >-
  Explicit, governed project memory retrieval and writeback for any AI coding
  agent across sessions and tools. Use when the user asks to remember a project
  decision or rule, recall prior lessons or gotchas, correct outdated memory,
  inspect memory state, or coordinate durable knowledge across agent sessions.
  Do not use for ordinary transient questions, routine coding where memory is
  not relevant, or first-time connection and installation.
version: 1.0.0
tags:
  - memory
  - agent-memory-bridge
  - recall
  - writeback
  - project-scope
---

# AMB

## One Cut

Explicit, governed project memory retrieval and writeback for any AI coding agent across sessions and tools.

Agent Memory Bridge (AMB) is the durable memory and signal authority. This skill is the everyday procedure for using it. Memory explains **why** a decision, rule, or gotcha exists. Live code, config, and tests show **what** is true now.

Contract baseline: AMB **v0.36.0**, durable schema **v12**, exactly **17** public MCP tools. There is no automatic learning and no 18th tool. Tool names below are the public MCP names (`recall`, `store`, …). Clients may prefix them (`agentMemoryBridge_recall`). The prefix is a client label, not a different tool and not extra authority.

## When to use

- The user asks to remember a project decision, rule, constraint, or preference.
- The task depends on prior lessons, gotchas, or domain notes.
- A stored record is outdated, contradictory, or mis-tagged and must be corrected.
- The user wants a compact look at what a namespace already holds.
- Work continues across sessions or tools and the durable facts should travel with the project, not the chat.

## When NOT to use

- Ordinary transient questions that will not matter next session.
- Routine coding where prior memory is not relevant to the change.
- First connection, install, `project init`, doctor, or verify. Route that to `amb-connect`.
- Tracked episode ledgers and worker handoffs, unless the task explicitly needs them. Those live in [references/advanced_modes.md](references/advanced_modes.md).

## Core loop

Default to the six everyday tools: `recall`, `browse`, `stats`, `store`, `revise`, `annotate`.

### 1. Resolve scope

Use one governed namespace. Do not guess it from the folder name or the chat.

- Inside a git checkout that was initialized with AMB: run `agent-memory-bridge project resolve .` (or the checkout path). Use the returned `namespace` only when `status` is `bound`. That value is `project:<slug>`.
- `no_binding`, `ambiguous_binding`, `not_a_repository`, and `repository_unavailable` are not a namespace. Do not invent one. Initialization belongs to `amb-connect`.
- If the user names a scope, use that explicit namespace: `project:<name>`, `domain:<name>`, or `global`.
- Repository-free work (bots, shared practices, operating rules) does not go through `project resolve`. See [references/scope_and_namespaces.md](references/scope_and_namespaces.md).

`project resolve` is read-only. It does not create a binding, and caller tags, workspace labels, or prompt text cannot select identity.

### 2. Recall in context

Search before browsing the web or rereading old chat.

```text
recall(
  namespace=<resolved namespace>,
  query="<task terms, not the whole prompt>",
  kind="memory",
  limit=5
)
```

- Keep `limit` at or below 5 unless the user asks for a wider scan.
- Prefer a targeted query. Empty-query `recall` is for filters or signal polling, not a memory dump.
- Use `browse` only when you do not yet know the query. Use `stats` for a count and health check, not for content.
- A text `recall` of durable memory can also return derived `repository_knowledge`. That block is rebuildable WHAT, not a stored decision.

### 3. Check live code against memory

Memory is not a substitute for the repo.

- If the record and the code agree, apply the record.
- If they disagree, the code wins for current behavior. Say so, then ask whether the memory should be revised.
- Do not "fix" code just to match a stale record, and do not silently rewrite the record to match the code.

### 4. Store only approved decisions

Write after the user confirms the fact, or after a gotcha is validated by a failing-then-fixed check.

- Explicit user intent ("remember that we pin schema v12") may be stored as a decision or constraint.
- An inferred lesson is a **proposal** until the user confirms it. Say what you would store; do not store it as authority.
- Use `kind="memory"`. Keep the payload compact. Templates: [references/record_templates.md](references/record_templates.md).
- Repeated identical `store` calls may deduplicate. If the response is `duplicate_with_new_metadata`, enrich with `annotate`. Do not store a second copy to sneak in a title or tag.

Workflows: [references/everyday_workflows.md](references/everyday_workflows.md).

### 5. Correct by superseding

When a stored fact changes, call `revise` with the predecessor id and the full replacement content. The old row stays for audit and gains a `supersedes` edge.

- Metadata-only enrichment (title, extra tags, provenance) uses `annotate`. Content stays unchanged.
- `forget` is not the correction path. Use it only for the narrow cases in [references/revision_and_correction.md](references/revision_and_correction.md).

## Everyday profile

| Tool | Role |
|---|---|
| `recall` | Targeted search of durable memory (or signal polling when explicitly coordinating). |
| `browse` | Recent items when you do not yet have a query. |
| `stats` | Counts, kind breakdown, top domains, oldest/newest timestamps. |
| `store` | Create one compact memory, or one signal when coordinating. |
| `revise` | New successor that supersedes an older memory. |
| `annotate` | Audited title, tag, or provenance enrichment without a new fact. |

Leave these for the modes that need them:

- `feedback` records whether a recall result helped. It does not change the memory or the ranking.
- `promote` reclassifies one existing row to `learn`, `gotcha`, or `domain-note` in place. It is a maintenance action, not the way to capture a new decision.
- `forget` and `export` are maintenance. `forget` deletes. `export` copies a namespace out for reading or interchange.
- `begin_run`, `record_run_event`, `get_run`, and `complete_run` are a tracked work ledger. They do not replace project memory.
- `claim_signal`, `extend_signal_lease`, and `ack_signal` move coordination state. They are not durable truth.

Full matrix: [references/tool_matrix.md](references/tool_matrix.md).

## Redlines

- Never dump conversational transcripts, chat history, hidden reasoning, or secrets into memory.
- Never treat an unverified inferred lesson as durable authority. Confirm it with the user first.
- Never silently overwrite contradictory memory. `revise` links the successor to the predecessor. A second `store` of a conflicting claim creates a parallel record.
- Never pass signal-only parameters as if they applied to durable memory. Do not send `ttl_seconds`, `expires_at`, or `signal_status` on `kind="memory"` calls. Omit them. The MCP boundary may null a placeholder, but the lower-level contract stays strict, and a placeholder can still hide results.
- Never confuse a client tool allowlist with server authorization. A visible tool is not permission to write global rules, delete records, or mint a verified-success receipt. Ordinary MCP callers cannot mint verification receipts.

## References

- [references/tool_matrix.md](references/tool_matrix.md) — all 17 tools, inputs, outputs, and when to call them.
- [references/everyday_workflows.md](references/everyday_workflows.md) — session start, decisions, gotchas, inspection.
- [references/record_templates.md](references/record_templates.md) — decision, gotcha, constraint, procedure, domain-note, handoff.
- [references/revision_and_correction.md](references/revision_and_correction.md) — find, revise, annotate, and the narrow `forget` cases.
- [references/scope_and_namespaces.md](references/scope_and_namespaces.md) — git-bound projects vs repository-free scopes.
- [references/advanced_modes.md](references/advanced_modes.md) — tracked runs and coordination signals.
