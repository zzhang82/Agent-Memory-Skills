# Local stdio recipe

Use this when the host can launch a local process. For `claude-code`, `cursor`, `codex`, `cline`, and `vscode`, always preview first with `agent-memory-bridge connect <client> --dry-run` before running `agent-memory-bridge connect <client>` to write (in `v0.39.0`, omitting `--dry-run` writes immediately; `--yes` is accepted for CLI compatibility but is not a confirmation gate). For other hosts, show the generic snippet, confirm the target file, and let the operator apply it.

## 1. Install into an isolated virtualenv

Python 3.11 or newer. On Linux, `python3` may be the launcher.

```bash
python -m venv .amb-venv
python -c "import os; from pathlib import Path; print((Path('.amb-venv') / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')).absolute())"
```

Use the printed interpreter as `<venv-python>`:

```text
<venv-python> -m pip install agent-memory-bridge==0.39.0
<venv-python> -m agent_mem_bridge doctor
<venv-python> -m agent_mem_bridge verify
```

For an exact source checkout, use `<venv-python> -m pip install -e .` instead of the PyPI pin. `uvx` is optional and is not the baseline.

`doctor` checks the local install. `verify` runs an isolated stdio runtime. Neither proves the host loaded its config.

## 2. Choose one persistent home

Default when unset: `~/.local/share/agent-memory-bridge`.

For a shared pilot, set one absolute `AGENT_MEMORY_BRIDGE_HOME` and reuse it in every client. Do not point a new install at an old home unless the operator wants that existing database.

An optional config file can live at `~/.config/agent-memory-bridge/config.toml`. Copy from `config.example.toml` only if a non-default setting is required.

## 3. Generic host shape

```json
{
  "mcpServers": {
    "agentMemoryBridge": {
      "command": "<venv-python>",
      "args": ["-m", "agent_mem_bridge"],
      "env": {
        "AGENT_MEMORY_BRIDGE_HOME": "/absolute/path/to/shared-bridge-home",
        "AGENT_MEMORY_BRIDGE_DEFAULT_SOURCE_CLIENT": "generic",
        "AGENT_MEMORY_BRIDGE_DEFAULT_CLIENT_TRANSPORT": "stdio"
      }
    }
  }
}
```

No-argument `-m agent_mem_bridge` is stdio. Do not add HTTP flags to this command.

If the host calls the console script directly, the equivalent command is `agent-memory-bridge` with no arguments, using the same environment.

## 4. One-command connectors (`v0.39.0`) and other hosts

For the five supported clients, preview first with `--dry-run`, then run `connect` to merge the `agent-memory-bridge` entry (with `.amb-backup.bak` backup and automatic rollback) and run the 3-tier connection check:

```bash
<venv-python> -m agent_mem_bridge connect claude-code --dry-run
<venv-python> -m agent_mem_bridge connect claude-code
<venv-python> -m agent_mem_bridge connect cursor
<venv-python> -m agent_mem_bridge connect codex
<venv-python> -m agent_mem_bridge connect cline --scope user
<venv-python> -m agent_mem_bridge connect vscode
<venv-python> -m agent_mem_bridge connect cursor --check
```

| Host | Config path / mechanism | Notes |
|---|---|---|
| `claude-code` | `.mcp.json` (project) or `~/.claude.json` (user), `mcpServers.agent-memory-bridge` | Includes `"type": "stdio"` and `-I -m agent_mem_bridge`. |
| `cursor` | `.cursor/mcp.json` or `~/.cursor/mcp.json`, `mcpServers.agent-memory-bridge` | Preserves sibling servers (`playwright`, etc.). Protects existing HTTP entries unless `--force` is passed. |
| `codex` | `.codex/config.toml` or `~/.codex/config.toml`, `[mcp_servers.agent-memory-bridge]` | Targeted TOML section merge preserving `[features]` and other tables. Set `AGENT_MEMORY_BRIDGE_HOME` explicitly if the old database is `~/.codex/mem-bridge`. |
| `cline` | `--scope user` (`$CLINE_MCP_SETTINGS_PATH`, `~/.cline/data/settings/cline_mcp_settings.json`, or VS Code `globalStorage`) or `--config-path` | Sets `disabled: false` and `autoApprove: []`. Rejects project scope without `--config-path`. |
| `vscode` | `.vscode/mcp.json` (`servers`, `--vscode-format servers`) or Copilot `.mcp.json` / `~/.copilot/mcp-config.json` (`mcpServers`, `--vscode-format copilot`) | Includes `"type": "stdio"`. Rejects relative commands and unexpanded `${workspaceFolder}`. |
| OpenCode / Claude Desktop / Generic | Manual JSON config using section 3 above | Reload or restart the host after editing. |

Do not claim a GUI IDE has reloaded its config until `tier3_host_registration_status` is `host_cli_verified` or the reloaded host lists `store` and `recall`.

## 5. Dockerized stdio, only if the host runs Docker locally

```bash
docker run --rm -i \
  -e AGENT_MEMORY_BRIDGE_HOME=/data/agent-memory-bridge \
  -e AGENT_MEMORY_BRIDGE_DEFAULT_SOURCE_CLIENT=generic \
  -e AGENT_MEMORY_BRIDGE_DEFAULT_CLIENT_TRANSPORT=stdio \
  -v /absolute/path/to/bridge-home:/data/agent-memory-bridge \
  ghcr.io/zzhang82/agent-memory-bridge:0.39.0 \
  agent-memory-bridge serve --transport stdio
```

Keep stdin open. The mount must be a local filesystem, not NFS or CIFS. Prefer the Compose HTTP service in [docker_deployment.md](docker_deployment.md) for a shared remote authority.

## 6. Hand-off

Restart or reload the host. Continue with [tool profiles](tool_profiles.md) and [verification](verification_and_repair.md). Initialize a project only after the host lists the tools:

```text
<venv-python> -m agent_mem_bridge project init .
<venv-python> -m agent_mem_bridge project resolve .
```

`project init` proposes a namespace and waits for confirmation. `project resolve` only reads an existing binding.
