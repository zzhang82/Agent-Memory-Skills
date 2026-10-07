# Everyday workflows

Use the six-tool profile: `recall`, `browse`, `stats`, `store`, `revise`, `annotate`.

Resolve scope before any of these. Inside a bound git checkout:

```bash
agent-memory-bridge project resolve .
```

Continue only when `status` is `bound`. Otherwise stop and use the explicit namespace the user named, or route initialization to `amb-connect`. Namespace rules: [scope_and_namespaces.md](scope_and_namespaces.md).

Record shapes: [record_templates.md](record_templates.md).

## Start a session or task

1. Resolve the namespace.
2. Recall with the task's nouns, not the whole user prompt.

```text
recall(
  namespace="project:demo-app",
  query="release schema pin",
  kind="memory",
  limit=5
)
```

3. If the query was a guess and the result is empty, inspect before widening the search.

```text
stats(namespace="project:demo-app")
browse(namespace="project:demo-app", kind="memory", limit=10)
```

4. Read the live files the hits mention. Memory explains why; the repo shows what.
5. If a hit disagrees with the code, say which one you are following and do not rewrite either side silently.

Do not raise `limit` past 5 to "be thorough." A second, narrower query is cheaper than a dump.

`repository_knowledge` on a text recall is derived repository WHAT. Do not store it back as a decision.

## Capture a confirmed decision

Store only after the user asks to remember it, or confirms a proposal.

1. Recall first so you do not create a parallel record.

```text
recall(
  namespace="project:demo-app",
  query="public mcp tool count",
  kind="memory",
  limit=5
)
```

2. If a current record already states the decision, stop. If the same content comes back as a duplicate with new metadata, `annotate` instead of storing again.
3. If an older record states a different decision, `revise` that id. Do not `store` the new wording beside it.
4. If nothing matches, store a compact record.

```text
store(
  namespace="project:demo-app",
  kind="memory",
  title="Public MCP surface stays 17 tools",
  tags=["kind:decision", "authority:user-asserted", "lifecycle:active"],
  content="claim: The public MCP surface stays exactly 17 tools.\ntrigger: When proposing a new MCP tool or wrapper.\nfix_or_decision: Extend CLI or internal workflows instead of adding a tool.\nscope: project:demo-app\nconfidence: validated\nsource: user-direction"
)
```

Omit `ttl_seconds`, `expires_at`, and `signal_status`.

5. Tell the user the id that came back. Later correction needs that id.

An inferred lesson you have not confirmed is a proposal. Show the payload and wait.

## Capture a validated gotcha

A gotcha needs a symptom and a fix you actually checked. A hunch is not a gotcha.

1. Recall `kind:gotcha` or the symptom terms.
2. Reproduce or point at the check that failed, then the check that passed.
3. Store symptom, cause, and fix together.

```text
store(
  namespace="project:demo-app",
  kind="memory",
  title="Memory recall hidden by signal_status in direct storage queries",
  tags=["domain:retrieval", "symptom:empty-recall", "fix:omit-signal-status"],
  content="record_type: gotcha\nclaim: Passing signal_status on kind=memory direct repository queries hides real rows.\ntrigger: Memory recall via lower-level store APIs returns empty while stats shows entries.\nsymptom: Direct storage queries filter out memories when signal_status is present.\ncause: signal_status placeholder fields sent to lower-level storage repositories.\nfix_or_decision: Omit signal-only fields. While MCP boundary normalizes them, lower-level queries remain strict.\nscope: project:demo-app\nconfidence: observed\nsource: repo-validation"
)
```

If this only retitles an existing identical gotcha, `annotate`. If the fix changed, `revise` the old id and put the new symptom and fix in `replacement_content`.

Do not promote a fresh store in the same breath. `promote` is for an older row whose type should change in place. See [tool_matrix.md](tool_matrix.md).

## Inspect memory state

Use the smallest read that answers the question.

| Question | Call |
|---|---|
| How much is in this namespace? | `stats(namespace=...)` |
| What landed recently? | `browse(namespace=..., kind="memory", limit=10)` |
| What do we know about this topic? | `recall(..., query="...", kind="memory", limit=5)` |
| Which domain notes exist? | `browse(namespace="domain:release", kind="memory", limit=10)` |

Inspection does not include `export` unless the user wants a portable snapshot. `export` defaults to 100 rows and is a maintenance copy, not a thinking step.

If browse shows several records that contradict each other, do not merge them in chat and store a third. Name the ids and correct with `revise`. Procedure: [revision_and_correction.md](revision_and_correction.md).

## What these workflows do not do

- They do not install AMB or run `project init`.
- They do not open a run ledger or claim a signal. See [advanced_modes.md](advanced_modes.md).
- They do not write `feedback`. Ranking does not change because a result felt useful.
- They do not copy the chat into `content`.
