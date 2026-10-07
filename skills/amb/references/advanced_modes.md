# Advanced modes

Everyday memory does not need these tools. Use them when the user asks for a tracked episode or for workers to hand off live work.

They do not replace `store` / `recall` / `revise`. A run ledger is not a decision. A signal is not a belief.

Contract baseline: AMB v0.36.0. The server mints run ids and verification receipts. Callers pass handles back. There is no implicit current run.

## Tracked work (runs)

Tools: `begin_run`, `record_run_event`, `get_run`, `complete_run`.

### When to open a run

Open a run when the user wants an auditable episode: goal, events, and a declared outcome that can be reconnected after compaction.

Do not open a run to remember a project rule. That is `store` on the project namespace.

### Start

`workspace_key` is the declared scope, usually the same `project:<slug>` you would recall. It rejects cross-workspace access. It is not by itself an authorization check.

```text
begin_run(
  workspace_key="project:demo-app",
  goal="Record the release-note pin without adding a tool.",
  idempotency_key="<caller-generated retry key>",
  evidence_profile="observational",
  risk_level="low"
)
```

Keep the idempotency key stable across retries of the same start. The bridge stores only its SHA-256. An identical retry returns the same run and work-item ids. A retry with the same key and a different payload is rejected.

`memory_scopes` lists buckets the run claims it may use. Listing `global` does not grant a write.

`evidence_profile="governed-v2"` is the strict ledger. Later events must use `event_schema_version=2` and the compare-and-swap fields the server returns (`expected_database_epoch`, `expected_run_generation`, `expected_last_sequence`). Observational runs may stay on schema version 1.

`risk_level` of `high` or `critical` means a preflight review has to include a rollback plan.

### Append events

Pass the minted `run_id` every time. Events that attach to an active work item must provide `work_item_id` (or both `parent_work_item_id` and `work_item_goal` when starting a child work item via `work_item_started`).

```text
record_run_event(
  workspace_key="project:demo-app",
  run_id="<from begin_run>",
  work_item_id="<root work_item_id from begin_run>",
  event_type="observation",
  summary="README tool list matches the 17 server tools.",
  idempotency_key="<unique per event>"
)
```

Summaries are factual and bounded. The server rejects raw transcripts and hidden reasoning. `payload` and `evidence` are each limited to 32 KiB.

`memory_recalled`, `memory_applied`, and `memory_rejected` require `memory_attribution`. A recall receipt may be validated. It is not written into the ledger.

Child work items are created only with `work_item_started`. To create a child without an existing `work_item_id`, you must provide both `parent_work_item_id` and `work_item_goal` (with optional `owner_agent_id`). Other events that target a work item must pass the existing `work_item_id`.

#### Governed Run Requirements (`governed-v2`)

When `evidence_profile="governed-v2"` is used, strict invariants apply:
1. `begin_run` requires at least one structured entry in `acceptance_criteria`.
2. All `record_run_event` calls must use `event_schema_version=2`.
3. Event appends and completion require compare-and-swap (CAS) preconditions: `expected_database_epoch`, `expected_run_generation`, and `expected_last_sequence`.
4. State-changing work item events require `expected_work_item_status`.
5. `complete_run` with `outcome="verified_success"` requires a matching server-minted `verification_receipt_id`. Ordinary MCP agents cannot mint receipts; agent self-report cannot claim verified success.

If `expected_last_sequence` does not match, the append is rejected and nothing is written. Call `get_run` and retry with the current sequence.

### Reconnect

```text
get_run(
  workspace_key="project:demo-app",
  run_id="<from begin_run>",
  since_sequence=0,
  event_limit=100
)
```

Use this after compaction or a new session. Do not rebuild state from chat.

### Finish

```text
complete_run(
  workspace_key="project:demo-app",
  run_id="<from begin_run>",
  outcome="unverified",
  evaluator_type="agent",
  idempotency_key="<unique for this outcome>"
)
```

| Outcome | Rule |
|---|---|
| `verified_success` | Requires `verification_receipt_id` minted by the server. Ordinary MCP callers cannot mint it. Agent `evaluator_type` cannot establish this outcome. |
| `partial_success`, `unverified`, `failed`, `abandoned` | Agent-declared. Say what was not verified. |
| `user_corrected` | The user changed the conclusion. Pass `supersedes_outcome_id` when correcting the current head. |
| `regression` | Requires `regression_of_run_id`: a different run in the same workspace whose current outcome is `verified_success`. |

Outcomes are append-only. Correcting one supersedes the head; it does not edit the old row. Completing a run does not change memory ranking.

`verified_success` also requires no unresolved information gaps on that run. Do not claim it because tests looked green in chat.

## Coordination signals

Tools: `store` with `kind="signal"`, then `claim_signal`, `extend_signal_lease`, `ack_signal`.

Create the signal with `store`, including `ttl_seconds` or `expires_at` when the handoff should die on a deadline. Template: [record_templates.md](record_templates.md).

### Claim

```text
claim_signal(
  namespace="project:demo-app",
  consumer="reviewer-a",
  signal_id="<exact id>",
  lease_seconds=300
)
```

Omit `signal_id` to take the next eligible pending signal. Optional `tags_any` and `correlation_id` narrow that selection. Next-eligible uses a small fairness bias inside the oldest pending window so one poller does not always win.

Only the consumer that holds the lease should do the work.

### Extend

```text
extend_signal_lease(
  id="<signal id>",
  consumer="reviewer-a",
  lease_seconds=300
)
```

The consumer must be the current claimant. Time is added from the current lease end and never past the signal's hard expiry. If the lease already expired, extend fails; `claim_signal` again.

### Acknowledge

```text
ack_signal(
  id="<signal id>",
  consumer="reviewer-a"
)
```

`consumer` must match an active claim. Omit `consumer` only when the signal is still pending and unclaimed.

Ack means the handoff is done. It does not store a lesson. If the work produced a durable fact, `store` or `revise` that fact separately, then ack.

### Polling

Workers that poll use `recall`, not the claim tool:

```text
recall(
  namespace="project:demo-app",
  query="",
  kind="signal",
  signal_status="pending",
  since="<previous next_since or omit on first poll>",
  limit=5
)
```

`since` requires an empty query and `kind="signal"`. `next_since` marks later inserts. It does not fire when an older signal only changes status.

## Redlines

- Do not put durable decisions only in a run event. Events are the episode. Project memory is the belief.
- Do not mark `verified_success` without a server-minted receipt.
- Do not treat `memory_scopes`, a client allowlist, or `workspace_key` as permission.
- Do not send `ttl_seconds` or `expires_at` on memory writes while working beside this mode.
- Do not ack a signal you do not own when it has an active claim.
