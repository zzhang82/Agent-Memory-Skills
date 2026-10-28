# Record templates

Store compact field-oriented payloads. One record, one claim. Titles are short and stable. Tags are `key:value` labels, not sentences.

Write durable rows with `kind="memory"`. The handoff template is the exception: it is `kind="signal"`.

Do not put transcripts, secrets, raw diffs, or chain-of-thought into `content`.

## Anti-pollution filter: Structure over prose

Never store mechanical rules that can be enforced by a compiler, linter, type system, or test suite. Before storing a record with `kind="memory"`, ask:

1. *Can a linter catch it?* (Configure ESLint/Biome/Ruff; do not store in AMB)
2. *Can static types or runtime assertions enforce it?* (Harden TypeScript types or Pydantic validators; do not store in AMB)
3. *Is it an irreversible architectural decision, domain boundary, or external SDK gotcha?* (Store in AMB with explicit trigger, claim, and rationale)

Suggested tag families, only when they help retrieval:

```text
kind:decision | kind:gotcha | kind:constraint | kind:procedure | kind:domain-note | kind:handoff
authority:user-asserted | authority:repo-verified | authority:agent-inferred
lifecycle:active | lifecycle:draft
```

`authority:agent-inferred` is a proposal marker. Do not use it as if the user had confirmed the claim.

`promote` may later reclassify a row to `learn`, `gotcha`, or `domain-note`. You do not need to call it to store a good record. Capture with `store`. Change a fact with `revise`.

## Decision

Use when the user confirmed a choice that should survive the session.

```text
claim: <one sentence>
trigger: <when an agent should apply it>
fix_or_decision: <the choice>
scope: <namespace>
confidence: validated
source: user-direction
```

Example store:

```text
store(
  namespace="project:demo-app",
  kind="memory",
  title="SQLite stays the durable authority",
  tags=["kind:decision", "authority:user-asserted", "lifecycle:active"],
  content="claim: SQLite/WAL rows stay the durable authority.\ntrigger: When adding a cache, export, or compiled context view.\nfix_or_decision: Derived views must not become a second source of truth.\nscope: project:demo-app\nconfidence: validated\nsource: user-direction"
)
```

## Gotcha

Use for a repeated failure with a checked symptom and fix.

```text
claim: <the pitfall>
trigger: <when it appears>
symptom: <what the agent observes>
cause: <why>
fix_or_decision: <what to do instead>
scope: <namespace>
confidence: observed | validated
source: live-debugging | repo-validation
```

Example:

```text
record_type: gotcha
claim: Signal-only placeholder fields were sent on direct storage queries.
trigger: Lower-level repository query fails validation or returns empty results despite stored memory.
symptom: Direct storage queries filter out memories when signal_status is present.
cause: Client wrapper sent signal lifecycle placeholder fields to direct repository APIs.
fix_or_decision: Keep signal-only fields omitted for kind="memory". While MCP boundary drops placeholders, direct storage stays strict.
scope: project:demo-app
confidence: observed
source: live-debugging
```

Tags that earn their keep: `symptom:<slug>`, `fix:<slug>`.

## Constraint

Use for a hard boundary the user set: what must not change, what is out of scope, what must stay pinned.

```text
claim: <the boundary>
trigger: <when someone is about to cross it>
fix_or_decision: <refuse or stay inside this line>
scope: <namespace>
confidence: validated
source: user-direction
```

Example:

```text
store(
  namespace="project:demo-app",
  kind="memory",
  title="Do not add MCP tool 18",
  tags=["kind:constraint", "authority:user-asserted", "lifecycle:active"],
  content="claim: The public MCP surface stays exactly 17 tools on schema v12.\ntrigger: When a design adds a packet, setup, or learning tool.\nfix_or_decision: Keep the new behavior in the CLI or an internal workflow.\nscope: project:demo-app\nconfidence: validated\nsource: user-direction"
)
```

## Procedure

Use for a stable how-to that is shorter than a skill and specific to this scope. Link out; do not paste the skill.

```text
claim: <what procedure is now the default>
trigger: <when to follow it>
fix_or_decision: <ordered steps, one line each>
scope: <namespace>
confidence: validated
source: user-direction | repo-validation
```

Example content:

```text
claim: Release notes are checked against the public tool list before tagging.
trigger: When cutting a release that mentions MCP tools.
fix_or_decision: 1. Read the server tool tuple. 2. Compare README tool names. 3. Stop if the count is not 17.
scope: project:demo-app
confidence: validated
source: repo-validation
```

If the procedure is reusable across projects, prefer a skill plus a short pointer record over a long memory row.

## Domain note

Use after several records in one domain agree and a single routing summary will save future recalls. Store it in `domain:<name>`, not in every project.

```text
topic: <domain>
pattern: <what keeps recurring>
default_practice: <what to do by default>
common_failure_modes: <short list>
routing_or_judgment: <how the next agent should choose>
scope: domain:<name>
confidence: observed | validated
source: synthesized-from-multiple-records
```

Example:

```text
store(
  namespace="domain:release",
  kind="memory",
  title="Release surface checks",
  tags=["kind:domain-note", "authority:repo-verified", "lifecycle:active"],
  content="topic: release surface\npattern: Tool-count drift shows up in README and announcements before schema changes.\ndefault_practice: Treat schema v12 and 17 public tools as the pin until the user changes it.\ncommon_failure_modes: counting client prefixes as extra tools, documenting CLI commands as MCP tools\nrouting_or_judgment: Recall this domain note when a task mentions tools, schema, or release notes.\nscope: domain:release\nconfidence: validated\nsource: synthesized-from-multiple-records"
)
```

Do not synthesize a domain note from a single session.

## Handoff

A handoff is coordination state. It expires. It is not a decision.

```text
store(
  namespace="project:demo-app",
  kind="signal",
  title="Review the schema pin note",
  tags=["kind:handoff", "workflow:release"],
  correlation_id="release-2026-10-07",
  ttl_seconds=86400,
  content="event: review-needed\nsummary: Schema pin note is stored and ready for review.\nowner: reviewer\nnext_action: Recall project:demo-app for the schema pin, then ack this signal.\nscope: project:demo-app"
)
```

`ttl_seconds` or `expires_at` belongs on this call only. Claiming and acknowledging use `claim_signal` and `ack_signal`, documented in [advanced_modes.md](advanced_modes.md).

## Quick classifier

| You have | Store as |
|---|---|
| A confirmed choice | decision, `kind="memory"` |
| A checked failure and fix | gotcha, `kind="memory"` |
| A do-not-cross boundary | constraint, `kind="memory"` |
| A short repeated how-to | procedure, `kind="memory"` |
| A synthesis of several records | domain-note in `domain:<name>` |
| Work for another agent to pick up | handoff, `kind="signal"` |
| A changed fact | do not use these templates with `store`; `revise` the old id |
