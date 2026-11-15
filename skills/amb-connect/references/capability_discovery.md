# Capability discovery

AMB v0.39 is an MCP memory service that ships verified connectors and a 6×5 trigger matrix for five clients (`claude-code`, `cursor`, `codex`, `cline`, `vscode`) and supports generic stdio or Streamable HTTP MCP for any other host (OpenCode, Claude Desktop, Hermes, Antigravity, bots, or custom agents). Discover the host before choosing a transport.

Ask the operator, or inspect the host's own docs and config, for each row. Record `yes`, `no`, or `unknown`. Do not fill unknown cells from an old per-client adapter.

## Capability matrix

| Capability | What to establish | If yes | If no |
|---|---|---|---|
| Local subprocess | Can the host launch a command with args, env, and a working directory, then speak MCP over stdin/stdout? | Use local stdio. | Local AMB cannot be embedded this way. |
| Streamable HTTP MCP | Can the host connect to a remote MCP endpoint and send a bearer header? | Use the existing or new HTTP authority. | Do not invent a REST client. |
| Skill loading | Can the host load `amb-connect` now and `amb` after connection? | Keep this skill for connection only. | Put the equivalent instructions in the host's normal instruction channel. |
| Lifecycle hooks | Can the host run a command on session start, task prompt, compaction, or stop, and pass one JSON object on stdin? | Lifecycle wiring is optional. | Skip hooks. Plain MCP is complete. |
| Tool filtering or approvals | Can the host expose a named subset or require approval before a tool call? | Apply a profile. | Expose the server surface and tell the agent which tools are in scope. |
| Local checkout | Is the project worktree present on the machine that runs AMB or the hook? | `project init` and local capture can resolve that checkout. | Remote HTTP can still serve memory. Do not enable capture. |

## How to detect without pretending Core knows the host

1. Find the host's MCP settings. For `claude-code`, `cursor`, `codex`, `cline`, and `vscode`, `agent-memory-bridge connect <client> --dry-run` previews the exact native config merge (`mcpServers`, VS Code `servers`, or Codex `[mcp_servers.agent-memory-bridge]`). For other hosts, inspect the host's own MCP config format.
2. Test subprocess support with `connect <client> --check` (for supported clients) or read the host's MCP docs for "stdio" or "local command".
3. Test HTTP support by looking for a URL field plus custom headers. SSE-only or legacy HTTP clients are not automatically Streamable HTTP clients.
4. Test hooks by checking `agent-memory-bridge triggers matrix` (for the 5 supported clients) or finding an event runner that can execute `<venv-python> -m agent_mem_bridge lifecycle-hook` and pipe JSON to stdin. A webhook that expects `POST /store` is not a hook.
5. Test filtering by finding an allowlist, enabled-tools list, or approval policy. If none exists, say so.
6. Test checkout locality with the host's working directory. A bot running on another machine does not have the operator's laptop checkout.

## Host classes

Use these only as discovery questions. They are not certified integrations.

| Host class | Usually ask |
|---|---|
| Desktop coding agent (Codex, Claude Desktop, Cursor, VS Code-style clients) | Which user or project config file launches stdio? Does reload require a full restart? Can it allowlist tool names? |
| OpenCode and similar local coding runtimes | Does this project or user config have an MCP server entry with `command`, `args`, and `env`? Are skills loaded from a skills directory? |
| Bot or remote agent (Grok bot, Dots, hosted custom agent) | Can it reach the authority only over HTTPS or an authenticated tunnel? Can it set `Authorization`? It usually cannot run a local hook against the operator's checkout. |
| Custom agent | Does its MCP client implement stdio, Streamable HTTP, or neither? If neither, stop. Do not add a private REST shim. |

Historical v0.35 adapters and the Codex Stop capture trial belong to tag `v0.35.0`. Use `v0.39.0`'s `connect` and `triggers` CLI commands for the 5 supported clients rather than copying v0.35 files.

## Minimum record before continuing

```text
host:
host_version:
subprocess_stdio: yes | no | unknown
streamable_http: yes | no | unknown
skill_loading: yes | no | unknown
lifecycle_hooks: yes | no | unknown
tool_filter_or_approval: yes | no | unknown
local_checkout_visible_to_amb: yes | no | unknown
existing_authority: none | local home | remote URL
```

If both transports are possible, prefer an authority that already exists over creating a second database.
