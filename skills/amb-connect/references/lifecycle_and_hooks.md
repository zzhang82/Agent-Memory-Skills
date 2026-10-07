# Lifecycle and hooks

Lifecycle is optional. A connected MCP client does not need it. v0.36 supplies one host-neutral command and does not ship client plugins or hook manifests.

```bash
<venv-python> -m agent_mem_bridge lifecycle-hook
```

The process reads one JSON object from stdin and writes one JSON object to stdout. Empty, invalid, or non-object input returns `{"decision":"ignore","context":""}`.

The host must translate its own event into this generic object. Vendor keys make the event `ignore`: `hook_event_name`, `event`, `host`, `last_assistant_message`, `transcript_path`, and `hookSpecificOutput`. Core does not read transcripts or certify the host.

## Accepted input

```json
{
  "kind": "task_prompt",
  "cwd": "/absolute/path/to/project",
  "session_id": "session-123",
  "prompt": "How do we run tests in this repo?"
}
```

| Field | Required | Meaning |
|---|---|---|
| `kind` | yes | One of `session_start`, `task_prompt`, `compaction`, `ignore`, `capture`. Anything else is `ignore`. |
| `cwd` | for project scope | Checkout used to resolve the bound project. The caller does not choose the namespace. |
| `session_id` | for repeat suppression and capture | Bounded session identity. |
| `prompt` | for `task_prompt` | Current task text. It is not archived as a transcript. |
| `source` | no | `compact` on `session_start` requests continuity instead of a memory dump. |
| `turn_id` | for `capture` | Required with `session_id` before a candidate can be stored. |
| `visible_artifact` | for `capture` | One `memory.visible_artifact.v1` object, at most 4,000 UTF-8 bytes. |

Caller `namespace`, tags, decision, or candidate status cannot retarget or approve a write.

## Event behavior

| `kind` | Result |
|---|---|
| `session_start` | Resolve the project. Do not dump memory. With `source="compact"`, return continuity context. |
| `task_prompt` | Recall at most once when the prompt needs project memory. An exact repeated prompt in the same session is suppressed. |
| `compaction` | Maintain continuity without a fresh recall. |
| `ignore` | No memory action. |
| `capture` | Propose one hidden `needs_review` candidate on the local authority. It does not promote anything. |

Task-time recall and capture are different lanes.

- Recall can use the selected local database or, when `AGENT_MEMORY_BRIDGE_AUTHORITY_URL` is set, one remote `recall` over Streamable HTTP.
- Remote recall errors propagate. The hook must say AMB was unavailable and must not present that as "no matching memory".
- Unbound or ambiguous project scope fails closed for recall. It does not guess a namespace from the directory name.

## Capture limits

`capture` stores a candidate only when all of these are true:

- the checkout resolves to one bound project
- the selected authority mode is local and available
- `session_id` and `turn_id` are present
- `visible_artifact.schema` is `memory.visible_artifact.v1`
- the artifact is a supported class with its required fields

Supported classes are `decision` and `constraint` with claim and reason, a validated `gotcha` with symptom and fix, `user_correction` of an identified record, and `handoff` with a bounded claim and reason. Transcripts, hidden reasoning, secrets, status chatter, and generic summaries produce no candidate.

Remote authority produces no capture candidate. There is no local-database fallback. A capture error is not a successful zero-write result.

Example artifact:

```json
{
  "schema": "memory.visible_artifact.v1",
  "artifact_id": "decision-1",
  "artifact_class": "decision",
  "claim": "Keep write-side capture in review until a person accepts it.",
  "reason": "Unreviewed proposals are not trusted project guidance.",
  "scope": "project"
}
```

Ordinary `recall`, `browse`, and `export` hide the `needs_review` lane. `promote` still refuses a learning candidate. Explicit MCP `store` is unchanged.

## Host wiring sketch

Only when the host can run a command and pipe JSON:

```text
on task prompt:
  stdin = {"kind":"task_prompt","cwd":"<checkout>","session_id":"<id>","prompt":"<text>"}
  command = <venv-python> -m agent_mem_bridge lifecycle-hook
  inject stdout "context" only when decision is not ignore or skip
```

For a remote recall hook, set `AGENT_MEMORY_BRIDGE_AUTHORITY_URL` and `AGENT_MEMORY_BRIDGE_HTTP_TOKEN_FILE` in that command's environment. Do not point the same hook at a second local home.

Do not wire `capture` on a remote authority. Do not pass raw transcripts as `prompt` dumps or `visible_artifact`.
