# Lifecycle and hooks

Lifecycle is optional. A connected MCP client does not need it. v0.38 supplies one host-neutral command and does not ship client plugins or hook manifests.

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

## Trigger moments and host mapping

The `amb` skill lists six trigger moments. A skill alone does not make an agent act at those moments; the host has to remind it. This section maps each moment to a host-neutral event, so any harness can wire it.

| Moment | Host-neutral event | How to serve it |
|---|---|---|
| Start of a task in a project | session start | `lifecycle-hook` with `kind: "session_start"` |
| Why / earlier work / bug intent | user prompt submitted | `lifecycle-hook` with `kind: "task_prompt"`, or a host-side keyword reminder |
| First file change of the session | before a write tool runs | host-side reminder only |
| Two failed attempts at the same fix | after a tool fails | host-side reminder only |
| Handoff to another agent | before a subagent or worker starts | put namespace and recalled ids in the handoff text |
| End of work that changed files | agent is about to stop | host-side consolidate reminder only |

"Host-side reminder" means the hook injects one line of context that asks the agent to run the step itself. It is not a `lifecycle-hook` kind. Do not send `first_write`, `failure`, or `stop` as a `kind`; core treats unknown kinds as `ignore`.

### Reminder rules

These rules keep reminders useful in any host:

- **Remind, do not act.** A reminder never calls `store`, `revise`, or `forget`. The consolidate reminder asks the agent to list candidates and wait for the user.
- **Once per session.** Keep a small per-session flag so the first-write and consolidate reminders fire at most once. Repeated reminders train the agent to ignore them.
- **Fail open.** Any error in the hook allows the tool or the stop. A memory reminder must never trap a session.
- **No stop loops.** If the host marks a stop that a hook already blocked once (for example a `stop_hook_active` flag), allow it.
- **Skip scratch paths.** Writes under temporary folders are not project changes.
- **Watch shell writes.** In permissive modes agents often write files through the shell (`echo >`, heredocs, `sed -i`). A write reminder that matches only file-edit tools misses them. Matching shell commands needs a heuristic, and it will misfire (for example a heredoc piped into an interpreter). Treat write counts as approximate.
- **Say when AMB is down.** A failed recall is "AMB unavailable", not "no matching memory".

### Host mechanisms

Hosts expose these events under different names. Use the host's own documentation for exact names and output formats. The rows below are a starting point, not certification.

| Host type | Mechanism | Notes |
|---|---|---|
| CLI agents with a hook config (for example Claude Code) | Command hooks on session start, prompt submit, pre-tool, and stop events | Claude Code example, checked on 2026-11-09: `SessionStart`, `UserPromptSubmit`, `PreToolUse` (match the edit tools and the shell tool), `Stop`. Context is returned as `hookSpecificOutput.additionalContext`. A one-time stop block is returned as `{"decision":"block","reason":...}`. |
| IDE agents with a hooks file (for example Cursor and its CLI agent) | Hook entries for session start, prompt submit, after tool use, and stop | Cursor example, checked against Cursor docs on 2026-11-09: `beforeSubmitPrompt` can only allow or block, and `preToolUse` can only allow or deny, so neither can add context. Add context at `sessionStart` and `postToolUse` with `additional_context`. Record prompt intent at submit and remind on the next `postToolUse`. Give the first-write reminder after the first write. For the end-of-work pass, return `followup_message` from `stop` and set `loop_limit: 1`. The CLI agent reads the same user-level `~/.cursor/hooks.json`. |
| Agents with a plugin API | Plugin event handlers | Same events, same reminder rules. |
| Hosts with no hook support | The instruction file the host always loads (for example `AGENTS.md`) | Copy the trigger table from the `amb` skill. This is weaker: the agent must remember it unaided. |

Prove a wiring with a fresh session, not by reading the config. Start a new session, make one change in a project folder, and confirm the reminder text reached the agent.
