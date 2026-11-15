---
name: amb-connect
description: Use when connecting Agent Memory Bridge (AMB) v0.39 to an agent host, running one-command connectors or the 3-tier connection check for Claude Code, Cursor, Codex, Cline, or VS Code, choosing local stdio or remote Streamable HTTP, deploying the official Docker authority, limiting exposed MCP tools, wiring packaged per-client triggers or generic lifecycle hooks, or diagnosing a disconnected memory client. Do not use for ordinary store, recall, or project memory work after the client is already connected.
version: 1.2.0
metadata:
  skill-type: integration
  authority: agent-memory-bridge
  amb-version: 0.39.0
  schema: v12
  public-mcp-tools: 17
  transports:
    - stdio
    - streamable-http
---

# amb-connect

## One Cut

Discover what the agent host can launch, connect it to one existing or newly deployed AMB authority (via `agent-memory-bridge connect <client>` for the 5 supported clients or manual MCP config for other hosts), expose only the needed MCP tools, optionally wire per-client triggers or host-neutral lifecycle hooks, and prove memory survives a fresh session.

This skill connects a host. The `amb` skill uses an already connected bridge.

Contract source: Agent Memory Bridge `0.39.0`, schema v12, exactly 17 public MCP tools. Legacy `setup` and `config` remain retired. In `v0.39.0`, `agent-memory-bridge connect <claude-code|cursor|codex|cline|vscode>` provides backup-backed configuration merging, a three-tier connection check (`tier1_config_valid`, `tier2_server_spawn_verified`, `tier3_host_registration_status` with values `not_checked`, `host_reload_required`, `host_cli_verified`), and a synthetic two-process bridge check (`connect --bridge-check` in an isolated temporary workspace), while `agent-memory-bridge triggers {matrix,install,test}` and `trigger-hook --client <client>` provide packaged per-client trigger reminders across an explicit 6×5 capability matrix. Other hosts (OpenCode, Claude Desktop, Grok bots, Dots, custom agents) use the generic stdio or Streamable HTTP recipes.

**Write-safety note for `connect` and `triggers install` in `v0.39.0`**: Unlike `project init` (which prompts unless `--yes` is passed), a bare `connect <client>` or `triggers install <client>` writes immediately (`--yes` is accepted as a non-interactive compatibility flag, not a confirmation gate; `connect <client> --check` is read-only and does not write; `connect --bridge-check` writes only inside its isolated temporary workspace). Always run with `--dry-run` first to preview changes before running the bare write command.

## When to use

- A host such as OpenCode, Codex, a Grok bot, Dots, Claude Desktop, Cursor, or a custom agent needs an AMB MCP server.
- An existing local home or remote Streamable HTTP authority should be reused.
- A new local virtualenv or official Docker authority must be deployed.
- Tool exposure, approvals, or optional lifecycle hooks need configuration.
- Memory appears disconnected, a client lists the wrong tools, or a v0.36+ home cutover needs diagnosis.

## When not to use

- Everyday `store`, `recall`, `browse`, feedback, runs, or signals. Use `amb`.
- Project knowledge, Explore, Inspect, or teaching one decision after the client is already connected. Use `amb`.
- Replacing an existing production authority, migrating a database, or unbinding a project. Those are separate operator-approved operations.
- Building secondary wrapper daemons, packet compilers, or caching daemons between the host and AMB. Connect agent hosts directly to AMB via native MCP (stdio or Streamable HTTP).

## Five stages

### 1. Discover host capabilities

Record subprocess execution, Streamable HTTP MCP, skill loading, lifecycle hooks, tool filtering or approvals, and whether the project checkout is local. For `claude-code`, `cursor`, `codex`, `cline`, and `vscode`, use read-only `agent-memory-bridge connect <client> --dry-run` and `agent-memory-bridge triggers matrix`; for other hosts, inspect the host's native MCP config format.

Details: [capability discovery](references/capability_discovery.md).

### 2. Select one authority and transport

Check for an existing authority before creating one:

1. Existing local stdio home.
2. Existing remote Streamable HTTP endpoint.
3. New local virtualenv install.
4. New official Docker remote deploy.

Every client that should share memory uses that same authority. Do not open the database over NFS or SMB.

Details: [transports and auth](references/transports_and_auth.md), [local stdio](references/local_stdio_recipe.md), [remote HTTP](references/remote_http_recipe.md), [Docker](references/docker_deployment.md).

### 3. Set the tool profile and permissions

Choose Everyday (6), Read-only (3), Tracked Work (+4), Signals (+3), Full (17), or a custom subset. Apply the subset in the host allowlist or instructions when the host supports it.

A client filter is not server authorization. A configured bearer token grants the whole 17-tool surface, including mutation and export.

Details: [tool profiles](references/tool_profiles.md).

### 4. Wire triggers or lifecycle hooks only when the host can run them

Optional. For `claude-code`, `cursor`, `codex`, `cline`, and `vscode`, inspect the 6×5 capability matrix and install packaged per-client triggers:

```bash
<venv-python> -m agent_mem_bridge triggers matrix
<venv-python> -m agent_mem_bridge triggers install <client> --dry-run
<venv-python> -m agent_mem_bridge triggers install <client>
<venv-python> -m agent_mem_bridge triggers test <client>
```

For the four hook-capable clients (`claude-code`, `cursor`, `codex`, `vscode`), the installed hook entries invoke `<venv-python> -m agent_mem_bridge trigger-hook --client <client>`, which translates vendor hook JSON (`hook_event_name`, `tool_name`, `stop_hook_active`, `loop_count`) outside `lifecycle-hook` into each host's exact output schema (`hookSpecificOutput.additionalContext`, `additional_context`, `followup_message`, `additionalContext`). `cline` installs managed instruction files only and has no `trigger-hook` runtime envelope.

For generic custom hosts that pipe host-neutral JSON, use:

```bash
<venv-python> -m agent_mem_bridge lifecycle-hook
```

It reads one generic JSON object on stdin. Accepted `kind` values are `session_start`, `task_prompt`, `compaction`, `ignore`, and `capture` (vendor keys such as `hook_event_name` return `ignore`).

Task-time recall can use the selected local or remote authority. Write-side `capture` is local-authority only in v0.39. Remote authority produces no candidate and does not fall back to a local database.

Details, rules, and 6×5 host mapping: [lifecycle and hooks](references/lifecycle_and_hooks.md#trigger-moments-and-host-mapping).

### 5. Verify, then run the two-session first win

1. Server & connector check: run `doctor`, `verify`, and for supported clients `connect <client> --check` (`tier1_config_valid`, `tier2_server_spawn_verified`, and `tier3_host_registration_status` in `not_checked | host_reload_required | host_cli_verified`). `connect --bridge-check --from-client <A> --to-client <B>` is an optional synthetic two-process round trip that writes fresh configs in a temporary workspace; it does not read or certify the operator's existing client configs on disk. Remote checks use `--url` and `--token-file` and do not open a local database.
2. Client: restart or reload when `tier3_host_registration_status` is `host_reload_required`, then confirm the host itself lists the expected AMB tools (`store` and `recall`).
3. First win: in session A, explicitly `store` one non-secret decision. Close it. In a fresh session B against the same authority, `recall` it and show the AMB result.

`doctor`, `verify`, and `tier2_server_spawn_verified` do not prove a GUI IDE reloaded its config after a file edit; only `host_cli_verified` or the reloaded host's own tool list proves live host registration.

Details: [verification and repair](references/verification_and_repair.md).

## Redlines

- Never silently fall back to a local database when a remote authority URL fails. Fail closed and say AMB was unavailable. An error is not an empty recall.
- Never invent REST endpoints such as `POST /store`. AMB is JSON-RPC over stdio, or standard MCP Streamable HTTP at `/mcp`. `/healthz` and `/readyz` are process checks only.
- Never claim a client tool allowlist, instruction, or approval prompt is a server-side security boundary.
- Never attempt remote write-side capture. v0.39 Core stores a capture candidate only when a local authority is selected.
- Never delete or replace an existing database, run `docker compose down --volumes`, copy over a live home, or unbind a project without explicit operator confirmation.
- Never store secrets, bearer tokens, or private credentials in AMB.
- Never conflate `tier2_server_spawn_verified` (spawning the configured command over stdio) with `host_cli_verified` or a reloaded GUI IDE, and never claim native command hooks for `instruction_rule` cells (such as Cline).

## References

- [Capability discovery](references/capability_discovery.md)
- [Transports and auth](references/transports_and_auth.md)
- [Local stdio recipe](references/local_stdio_recipe.md)
- [Remote HTTP recipe](references/remote_http_recipe.md)
- [Docker deployment](references/docker_deployment.md)
- [Tool profiles](references/tool_profiles.md)
- [Lifecycle and hooks](references/lifecycle_and_hooks.md)
- [Verification and repair](references/verification_and_repair.md)
