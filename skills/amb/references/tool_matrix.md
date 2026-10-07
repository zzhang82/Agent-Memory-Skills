# AMB tool matrix

Baseline: AMB v0.36.0, schema v12, public MCP surface of exactly 17 tools, in this order:

`store`, `recall`, `browse`, `stats`, `forget`, `feedback`, `promote`, `annotate`, `revise`, `export`, `begin_run`, `record_run_event`, `get_run`, `complete_run`, `claim_signal`, `extend_signal_lease`, `ack_signal`.

Client prefixes (`agentMemoryBridge_store`) are allowlist labels. They do not add tools or authority.

Profiles used by the `amb` skill:

| Profile | Count | Tools |
|---|---|---|
| Everyday | 6 | `recall`, `browse`, `stats`, `store`, `revise`, `annotate` |
| Retrieval feedback | 1 | `feedback` |
| Maintenance | 3 | `forget`, `promote`, `export` |
| Tracked work | 4 | `begin_run`, `record_run_event`, `get_run`, `complete_run` |
| Coordination | 3 | `claim_signal`, `extend_signal_lease`, `ack_signal` |

`project resolve` is a CLI read, not one of the 17 tools:

```bash
agent-memory-bridge project resolve .
```

Use the `namespace` field only when `status` is `bound`.

## Everyday (6)

### `recall`

Search durable memory, or poll signals when coordinating.

Required: `namespace`.

Common inputs: `query` (default `""`), `limit` (1–100, default 5), `kind` (`memory` or `signal`), `tags_any`, `session_id`, `actor`, `correlation_id`.

Signal-only inputs, omit for memory: `signal_status` (`pending`, `claimed`, `acked`, `expired`), `since` (polling cursor; requires an empty query and `kind="signal"`).

Optional: `evidence_context` with at most the keys `model`, `harness`, and `chat_template`. Labels are not authenticated and do not change rank.

Returns matching entries. A non-empty text recall of memory may include derived `repository_knowledge` (rebuildable WHAT, not a stored decision). Empty-query signal recall returns `next_since`; other modes return `next_since=null`. That cursor tracks later inserts, not status changes on older signals.

Invoke for a targeted lookup before external search. Everyday cap: `limit <= 5`.

### `browse`

List recent items when you do not yet have a query.

Required: `namespace`.

Inputs: `domain` (plain name, no `domain:` prefix), `kind`, `limit` (1–100, default 10). `signal_status` is signal-only.

Returns recent entries for those filters. It does not rank by relevance.

Invoke to see what a namespace holds, scan a domain, or confirm signals exist before writing a real query.

### `stats`

Health summary for one namespace.

Required: `namespace`. No query.

Returns total count, kind breakdown, top domains, and oldest/newest timestamps.

Invoke for "what is in this namespace?" Do not treat it as content.

### `store`

Create one memory or one signal.

Required: `namespace`, `content`. `kind` defaults to `memory`.

Memory inputs: `tags`, `title`, `session_id`, `actor`, `correlation_id`, and optional provenance (`source_app`, `source_client`, `source_model`, `client_session_id`, `client_workspace`, `client_transport`).

Signal-only inputs: `expires_at` (ISO-8601), `ttl_seconds` (integer > 0). Do not send them for `kind="memory"`. The MCP boundary nulls placeholders; direct storage stays strict.

Returns the entry id, timestamp, and duplicate information. Identical memory writes may deduplicate (`duplicate_with_new_metadata` means call `annotate`, not a second store). Signal writes stay append-like.

Invoke when the user confirmed a decision or a gotcha was validated. Do not store transcripts.

### `revise`

Create a successor memory that supersedes an older row.

Required: `id` (predecessor), `replacement_content` (the full new payload, not a patch).

Optional: `title`, `tags`, `actor`, `reason`, `provenance`.

**Reserved policy tags:** Callers cannot mint reserved tags: `candidate_status:`, `confidence:`, `control:`, `kind:`, `relation:`, `reviewed:`, `scope:`, `source:`, `status:`, or `validity:`. Use domain/component tags in `tags` and place classification in structured content.

Returns an envelope with `predecessor_id`, `successor_id`, and `result` (write-result metadata dict: `id`, `stored`, `duplicate`, `write_disposition`). The predecessor remains for audit with an exact `supersedes` edge and a revision receipt. This is not an in-place content edit.

Invoke when a stored fact changed. Do not `store` a conflicting parallel record.

### `annotate`

Enrich metadata without changing content or identity.

Required: `id`, and at least one of `title`, `tags`, or `provenance`.

Optional: `tags` (added; existing tags remain, reserved policy tags rejected), `title`, `provenance`, `actor`.

Returns an envelope containing the annotation audit record and `changed: true/false`. Content is unchanged.

Invoke after `duplicate_with_new_metadata`, or when only the title, tags, or provenance need an audit trail.

## Retrieval feedback (1)

### `feedback`

Append a judgment of one recalled result.

Required: `namespace`, `recall_receipt` (signed token from a durable text `recall`), `memory_id`, `result_rank` (1-based).

Inputs: `outcome` (required for votes and corrections: `helpful`, `misleading`, `outdated`, `not_applicable`, `not_used`; optional for retractions), `reason` (required for `misleading` and `outdated`), `feedback_type` (`vote` default, `correction`, `retraction`), `supersedes_feedback_id` (required for correction and retraction), `provenance`.

Returns an append-only feedback id. It does not mutate the memory, the recall set, or ranking.

Invoke only to record retrieval quality. To fix the fact itself, use `revise`.

## Maintenance (3)

### `forget`

Delete one entry by id.

Required: `id`.

Returns whether a row was deleted and the removed metadata when found.

Invoke only for accidental writes, secrets, or records that should not exist. Correction of a true fact is `revise`. See [revision_and_correction.md](revision_and_correction.md).

### `promote`

Reclassify one existing memory in place.

Required: `id`, `to_kind` (`learn`, `gotcha`, or `domain-note`).

Returns the same id with updated title, tags, and structured content.

Invoke when a stored record should be treated as a stronger type and the reflex layer has not promoted it. Do not use it to capture a new decision (`store`) or replace a changed fact (`revise`).

### `export`

Copy namespace content out as markdown, JSON, or text.

Required: `namespace`.

Inputs: `format` (`markdown` default, `json`, `text`), `query`, `kind`, `tags_any`, `limit` (1–500, default 100). `signal_status` is signal-only.

Returns a portable snapshot. The export is derived. It is not a second authority and not a training set.

Invoke for a human-readable dump or interchange. Do not use it as everyday recall.

## Tracked work (4)

Runs are an append-only episode ledger. The server mints ids. There is no implicit "current run"; pass `workspace_key` and `run_id` on every later call. Details: [advanced_modes.md](advanced_modes.md).

### `begin_run`

Start one run.

Required: `workspace_key`, `goal`, `idempotency_key`.

Common inputs: `evidence_profile` (`observational` default, or `governed-v2`), `risk_level` (`low`, `medium`, `high`, `critical`; high and critical preflight needs a rollback plan), `acceptance_criteria` (required for `governed-v2`), `constraints`, `non_goals`, `memory_scopes` (max 32; declaration is not authorization), `continuation_of_run_id`, digest fields, `provenance`.

Returns server-minted run and work-item ids. An identical idempotency retry returns the same handles and rejects a conflicting payload.

### `record_run_event`

Append one structured event.

Required: `workspace_key`, `run_id`, `event_type`, `summary`, `idempotency_key`.

`event_schema_version` is 1, or 2 for governed-v2. Governed-v2 also requires CAS preconditions: `expected_database_epoch`, `expected_run_generation`, and matching `expected_last_sequence`. State-changing events on work items require `expected_work_item_status`.

Work item attachment: events referencing a work item require `work_item_id`. To spawn a child work item via `work_item_started` without an existing id, pass both `parent_work_item_id` and `work_item_goal`.

Event types include `plan_created`, `work_item_started`, `checkpoint`, `observation`, `hypothesis`, `hypothesis_confirmed`, `hypothesis_rejected`, `tool_result`, `test_failure`, `decision`, `blocker`, `memory_recalled`, `memory_applied`, `memory_rejected`, `artifact_created`, `compaction_boundary`, `work_item_completed`, `work_item_failed`, `work_item_abandoned`, `preflight_review`, `test_result`, `risk_identified`, `information_gap`, `verification_result`, `work_item_resumed`, `blocker_resolved`.

`memory_recalled`, `memory_applied`, and `memory_rejected` require `memory_attribution`. Receipt tokens are validated and not persisted. Summaries must be factual. Raw transcripts and hidden reasoning are rejected. Payloads and evidence are each capped at 32 KiB.

Returns the appended sequence. Compare-and-swap mismatches reject the write.

### `get_run`

Read projections plus events after `since_sequence` (default 0).

Required: `workspace_key`, `run_id`. `event_limit` is 1–500, default 100.

Returns the current run, work items, and the ordered event page. Use it to reconnect after compaction. It does not set a current run.

### `complete_run`

Append an outcome revision.

Required: `workspace_key`, `run_id`, `outcome`, `evaluator_type`, `idempotency_key`.

Governed-v2 runs require CAS fields: `expected_database_epoch`, `expected_run_generation`, and `expected_last_sequence`.

Outcomes: `verified_success` (for governed runs, requires matching server-minted `verification_receipt_id`), `partial_success`, `unverified`, `user_corrected` (requires `supersedes_outcome_id`), `regression` (requires `regression_of_run_id` pointing at a different same-workspace run whose current outcome is `verified_success`), `failed`, `abandoned`.

Evaluator types: `agent`, `deterministic_verifier`, `human`, `system`. Agent self-report cannot establish `verified_success`. Corrections pass `supersedes_outcome_id`.

Returns the outcome head. Ranking and memory policy are unchanged.

## Coordination (3)

Signals are `kind="signal"` rows with a lifecycle. They are not durable beliefs. Create them with `store`, not with these tools.

### `claim_signal`

Take a lease on one pending signal.

Required: `namespace`, `consumer`. `lease_seconds` defaults to 300 and must be > 0.

Optional: `signal_id` (omit to claim the next eligible signal), `tags_any`, `correlation_id`.

Returns the claimed signal. Next-eligible selection uses a small fairness bias inside the oldest pending window.

### `extend_signal_lease`

Add time to a lease the caller already owns.

Required: `id`, `consumer`, `lease_seconds` (> 0).

Returns the extended lease. Extension starts from the current lease end when possible, never past hard expiry. An expired lease cannot be extended; claim it again.

### `ack_signal`

Mark the signal done so pollers stop treating it as active.

Required: `id`. `consumer` is required when an active claim exists and must match the claimant. Omit `consumer` only for a pending, unclaimed signal.

**Policy note on claim-required mode:** Under hardened configurations (such as Docker `hardened-local`), acknowledging an unclaimed pending signal may be rejected with `acked: false, reason: "claim-required"`. Callers must inspect the returned envelope to confirm `acked: true`.

Returns the acknowledged signal.

## Parameter boundary

| Parameter | Memory calls | Signal calls |
|---|---|---|
| `ttl_seconds`, `expires_at` | omit | `store` only |
| `signal_status` | omit | `recall`, `browse`, `export` filters |
| `since` | omit | empty-query `recall` polling |
| `kind="memory"` | everyday default | do not use for handoffs |

A client that shows all 17 tools has not authorized deletion, global writes, or verified-success receipts. Those still follow the tool rules above.
