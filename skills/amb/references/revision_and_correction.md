# Revision and correction

Durable facts change by succession, not by a quiet overwrite and not by a second conflicting `store`.

| Change | Tool | What happens |
|---|---|---|
| The claim, fix, or scope changed | `revise` | New row. Old row kept. Exact `supersedes` edge plus a revision receipt. |
| Title, tags, or provenance only | `annotate` | Same id. Content unchanged. Annotation is audited. |
| Same content, store reported new metadata | `annotate` | Do not store another copy. |
| Accidental, secret, or should-not-exist row | `forget` | Row deleted. Audit metadata returned when found. |
| A recall result was unhelpful | `feedback` | Shadow event only. The fact is untouched. |
| Type label should be stronger, content stands | `promote` | Same id, reclassified to `learn`, `gotcha`, or `domain-note`. |

## Find the predecessor id

1. Recall the narrowest query that should hit the old fact.

```text
recall(
  namespace="project:demo-app",
  query="public mcp tool count",
  kind="memory",
  limit=5
)
```

2. If the query misses, `browse` recent memory in that namespace and read titles.
3. Use the exact `id` from the result. Do not revise a record because the title looks similar.
4. If several live records disagree, revise the one the user identifies. Tell them about the others. Do not merge by inventing a new `store`.

Ids are opaque. Copy them; do not reformat them.

## Revise when the fact changed

`replacement_content` is the full new payload, not a diff.

```text
revise(
  id="<predecessor id from recall>",
  title="Public MCP surface stays 17 tools",
  tags=["domain:architecture", "topic:mcp-tools", "component:mcp-boundary"],
  reason="User pinned the v0.36 surface; older note said 12 tools.",
  replacement_content="record_type: decision\nclaim: The public MCP surface stays exactly 17 tools on schema v12.\ntrigger: When proposing a new MCP tool.\nfix_or_decision: Do not add tool 18. Keep extras in the CLI.\nscope: project:demo-app\nconfidence: observed\nsource: user-direction"
)
```

**Policy-tag warning:** Never pass reserved policy prefixes in caller `tags`: `candidate_status:`, `confidence:`, `control:`, `kind:`, `relation:`, `reviewed:`, `scope:`, `source:`, `status:`, or `validity:`. AMB's repository layer rejects caller attempts to add reserved policy tags (e.g. `status:pinned` or `kind:decision` will be rejected by the server). Put taxonomy in structured content (e.g. `record_type: decision`), and use `tags` only for domain/component labels (`domain:architecture`, `component:mcp`).

Optional `title` and `tags` default from the predecessor when omitted (retaining existing compatible tags). Pass them when the label should change with the fact.

The response envelope returns `predecessor_id`, `successor_id`, and a nested `result` dictionary with write-result metadata (`id`, `stored`, `duplicate`, `write_disposition`; for example `stored: true, duplicate: false` on fresh content, or `stored: false, duplicate: true` if content matches existing memory). The predecessor stays readable for audit with an exact `supersedes` edge and revision receipt. Future recalls prefer the successor. If a later recall still surfaces the old wording as current, do not store a third copy; inspect the link and ask before another revise.

Do not `revise` a signal. Signals expire or get acknowledged. See [advanced_modes.md](advanced_modes.md).

## Annotate when only metadata changes

Use `annotate` after `store` returns `duplicate_with_new_metadata`, or when updating display title, non-policy tags, or provenance on an existing memory without modifying its content.

`annotate` requires `id` and at least one enrichment field (`title`, `tags`, or `provenance`).

```text
annotate(
  id="<memory id>",
  title="Memory recall hidden by signal_status",
  tags=["domain:retrieval", "component:mcp-boundary"],
  actor="user"
)
```

Like `revise`, `annotate` rejects caller-minted reserved policy tags (`kind:`, `status:`, etc.). Existing tags remain; new tags are appended. The response envelope returns an auditable annotation receipt and `changed: true` (or `changed: false` if nothing was modified).

Use this when:

- `store` returns `duplicate_with_new_metadata`
- a title is vague but the claim is still right
- provenance should record who confirmed an existing claim

`annotate` does not add a supersession edge and does not rewrite `content`. If one field inside the content is wrong, that is a `revise`.

## When forget is required

`forget` is for rows that should not remain even as history.

Use it only when:

- the write was accidental (wrong namespace, test payload, duplicated draft the user wants gone)
- the content contains a secret, credential, or private data that should not sit in an audit predecessor
- the user explicitly says to delete that id rather than supersede it

```text
forget(id="<exact id>")
```

The response says whether anything was deleted.

Do not `forget` a record merely because it is old, stale, or wrong. Stale-but-real history is what `revise` preserves. Deleting it removes the audit trail the next agent would use to see why the successor exists.

Do not `forget` as cleanup after a successful `revise`.

## What not to do

- Do not `store` a "correction" beside the old record. That leaves two current claims.
- Do not `promote` to smuggle a content change. Promotion reclassifies; it is not a revision.
- Do not use `feedback` outcome `outdated` as a substitute for `revise`. Feedback does not change the stored fact or the ranking.
- Do not revise from memory of an id. Recall it in this session.
