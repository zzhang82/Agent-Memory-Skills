---
name: amb-connect
description: Use when connecting Agent Memory Bridge (AMB) v0.36 to an agent host, choosing local stdio or remote Streamable HTTP, deploying the official Docker authority, limiting exposed MCP tools, wiring optional lifecycle hooks, or diagnosing a disconnected memory client. Do not use for ordinary store, recall, or project memory work after the client is already connected.
version: 1.0.0
metadata:
  skill-type: integration
  authority: agent-memory-bridge
  amb-version: 0.36.0
  schema: v12
  public-mcp-tools: 17
  transports:
    - stdio
    - streamable-http
---

# amb-connect

## One Cut

Discover what the agent host can launch, connect it to one existing or newly deployed AMB authority, expose only the needed MCP tools, optionally wire host-neutral lifecycle hooks, and prove memory survives a fresh session.

This skill connects a host. The `amb` skill uses an already connected bridge.

Contract source: Agent Memory Bridge `0.36.0`, schema v12, exactly 17 public MCP tools. `setup` and `config` are gone. Core does not discover, write, or certify Codex, OpenCode, Claude, Cursor, or any other named client.

## When to use

- A host such as OpenCode, Codex, a Grok bot, Dots, Claude Desktop, Cursor, or a custom agent needs an AMB MCP server.
- An existing local home or remote Streamable HTTP authority should be reused.
- A new local virtualenv or official Docker authority must be deployed.
- Tool exposure, approvals, or optional lifecycle hooks need configuration.
- Memory appears disconnected, a client lists the wrong tools, or a v0.36 home cutover needs diagnosis.

## When not to use

- Everyday `store`, `recall`, `browse`, feedback, runs, or signals. Use `amb`.
- Project knowledge, Explore, Inspect, or teaching one decision after the client is already connected. Use `amb`.
- Replacing an existing production authority, migrating a database, or unbinding a project. Those are separate operator-approved operations.

## Five stages

### 1. Discover host capabilities

Record subprocess execution, Streamable HTTP MCP, skill loading, lifecycle hooks, tool filtering or approvals, and whether the project checkout is local. Do not guess a client config format Core no longer ships.

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

### 4. Wire lifecycle hooks only when the host can run them

Optional. The host launches:

```bash
<venv-python> -m agent_mem_bridge lifecycle-hook
```

It reads one generic JSON object on stdin. Accepted `kind` values are `session_start`, `task_prompt`, `compaction`, `ignore`, and `capture`.

Task-time recall can use the selected local or remote authority. Write-side `capture` is local-authority only in v0.36. Remote authority produces no candidate and does not fall back to a local database.

Details: [lifecycle and hooks](references/lifecycle_and_hooks.md).

### 5. Verify, then run the two-session first win

1. Server: `doctor` and `verify`. Remote checks use `--url` and `--token-file` and do not open a local database.
2. Client: restart or reload, then confirm the host itself lists the expected AMB tools.
3. First win: in session A, explicitly `store` one non-secret decision. Close it. In a fresh session B against the same authority, `recall` it and show the AMB result.

`doctor` and `verify` do not prove the host loaded its config.

Details: [verification and repair](references/verification_and_repair.md).

## Redlines

- Never silently fall back to a local database when a remote authority URL fails. Fail closed and say AMB was unavailable. An error is not an empty recall.
- Never invent REST endpoints such as `POST /store`. AMB is JSON-RPC over stdio, or standard MCP Streamable HTTP at `/mcp`. `/healthz` and `/readyz` are process checks only.
- Never claim a client tool allowlist, instruction, or approval prompt is a server-side security boundary.
- Never attempt remote write-side capture. v0.36 Core stores a capture candidate only when a local authority is selected.
- Never delete or replace an existing database, run `docker compose down --volumes`, copy over a live home, or unbind a project without explicit operator confirmation.
- Never store secrets, bearer tokens, or private credentials in AMB.
- Never claim a named client is certified. v0.36 examples are generic shapes the operator applies.

## References

- [Capability discovery](references/capability_discovery.md)
- [Transports and auth](references/transports_and_auth.md)
- [Local stdio recipe](references/local_stdio_recipe.md)
- [Remote HTTP recipe](references/remote_http_recipe.md)
- [Docker deployment](references/docker_deployment.md)
- [Tool profiles](references/tool_profiles.md)
- [Lifecycle and hooks](references/lifecycle_and_hooks.md)
- [Verification and repair](references/verification_and_repair.md)
