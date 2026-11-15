# Lifecycle and hooks

Lifecycle and trigger reminders are optional. A connected MCP client does not need them. In v0.39, AMB supplies two distinct layers:

1. **Packaged per-client trigger reminders (`triggers` and `trigger-hook`)** for `claude-code`, `cursor`, `codex`, `cline`, and `vscode` across an explicit 6×5 capability matrix. For the four hook-capable clients (`claude-code`, `cursor`, `codex`, `vscode`), `trigger-hook --client <client>` translates host-specific hook payloads (`hook_event_name`, `tool_name`, `stop_hook_active`, `loop_count`) outside `lifecycle-hook` into each host's exact reminder envelope. `cline` installs managed instruction files only and has no `trigger-hook` runtime envelope.
2. **Host-neutral lifecycle activation (`lifecycle-hook`)** for generic custom harnesses that pipe host-neutral JSON (`kind` in `session_start`, `task_prompt`, `compaction`, `ignore`, `capture`).

```bash
# Packaged per-client triggers (v0.39.0; preview with --dry-run before writing)
<venv-python> -m agent_mem_bridge triggers matrix
<venv-python> -m agent_mem_bridge triggers install <claude-code|cursor|codex|cline|vscode> --dry-run
<venv-python> -m agent_mem_bridge triggers install <claude-code|cursor|codex|cline|vscode>
<venv-python> -m agent_mem_bridge triggers test <client>
<venv-python> -m agent_mem_bridge trigger-hook --client <claude-code|cursor|codex|vscode>

# Host-neutral generic lifecycle hook
<venv-python> -m agent_mem_bridge lifecycle-hook
```

In `v0.39.0`, a bare `triggers install <client>` writes immediately (`--yes` is accepted for CLI compatibility, not a confirmation gate). Always preview with `--dry-run` first.

For `lifecycle-hook`, the process reads one generic JSON object from stdin and writes one JSON object to stdout. Empty, invalid, or non-object input returns `{"decision":"ignore","context":""}`.

The host must translate its own event into this generic object when calling `lifecycle-hook`. Vendor keys make `lifecycle-hook` return `ignore`: `hook_event_name`, `event`, `host`, `last_assistant_message`, `transcript_path`, and `hookSpecificOutput`. Never pipe raw Claude Code, Cursor, or Codex hook payloads into `lifecycle-hook`; use `trigger-hook --client <client>` for those hosts.

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

### Host mechanisms and the v0.39 6×5 capability matrix

In v0.39, `agent-memory-bridge triggers matrix` reports each of the 30 cells (`6 moments × 5 clients`) as `native_hook`, `deferred_hook`, `trust_gated_hook`, or `instruction_rule`:

| Client | Mechanism installed by `triggers install <client>` | Matrix breakdown across the 6 moments |
|---|---|---|
| `claude-code` | `.claude/settings.json` command hooks (`trigger-hook --client claude-code`) | All 6 moments are `native_hook`: `SessionStart`, `UserPromptSubmit`, `PreToolUse` (`Edit\|Write\|NotebookEdit\|MultiEdit\|Bash` and `Task\|Agent`), `PostToolUseFailure` (2x executed-error counter ignoring interrupts, permission denials, and empty errors), and `Stop` (one-time `{"decision":"block","reason":...}` when `not stop_hook_active`). Context is returned as `hookSpecificOutput.additionalContext`. |
| `cursor` | `.cursor/hooks.json` (`"version": 1`, `trigger-hook --client cursor`) | `session_start`, `first_write` (`postToolUse`), `repeated_failure` (`postToolUseFailure` 2x counter ignoring `permission_denied`), and `session_stop` (`stop` `followup_message` with `loop_limit: 1` and `loop_count == 0`) are `native_hook`. `prompt_intent` is `deferred_hook` (`beforeSubmitPrompt` records intent and returns `{"continue": true}`; next `postToolUse` injects `additional_context`). `subagent_handoff` is labeled `instruction_rule` (`subagentStart` is allow/deny only), but note the mechanism difference: `triggers install cursor` writes only `.cursor/hooks.json` (no markdown file) and injects the handoff rule inside the `sessionStart` hook's `additional_context` payload. If the `sessionStart` hook is disabled, that rule disappears unless also added to `AGENTS.md` or `.cursor/rules`. |
| `codex` | `.codex/hooks.json` + managed block in `AGENTS.md` | `session_start`, `prompt_intent`, and `session_stop` are `trust_gated_hook` (require `[features].hooks != false` in `config.toml` and interactive `/hooks` trust). `first_write`, `repeated_failure`, and `subagent_handoff` are `instruction_rule` in `AGENTS.md`. |
| `vscode` | `.github/hooks/amb-triggers.json` (`$COPILOT_HOME/hooks/amb-triggers.json` for user scope) + `.github/copilot-instructions.md` | `session_start`, `first_write` (`preToolUse`, always exits `0`), `repeated_failure` (`postToolUse` 2x counter), `subagent_handoff` (`subagentStart`), and `session_stop` (`agentStop`) are `native_hook` returning `additionalContext`. `prompt_intent` is `deferred_hook` (`userPromptSubmitted` ignores stdout -> flags state and injects `additionalContext` on next tool event). |
| `cline` | `.clinerules/amb-triggers.md` and `.cline/rules/amb-triggers.md` (user scope: `~/Documents/Cline/Rules/`, `~/.cline/rules/`, `~/Cline/Rules/`) | All 6 moments are `instruction_rule`. No native command hooks are claimed. |
| Other hosts with no hook support | The instruction file the host always loads (for example `AGENTS.md`) | Copy the trigger table from the `amb` skill. This is weaker: the agent must remember it unaided. |

Prove a wiring with `agent-memory-bridge triggers test <client>` (synthetic self-test) and a fresh live session. Start a new session, make one change in a project folder, and confirm the reminder text reached the agent.
