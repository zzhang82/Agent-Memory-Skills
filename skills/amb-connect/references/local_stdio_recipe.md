# Local stdio recipe

Use this when the host can launch a local process. AMB does not write the host config. Show the snippet, confirm the target file, then let the operator apply it.

## 1. Install into an isolated virtualenv

Python 3.11 or newer. On Linux, `python3` may be the launcher.

```bash
python -m venv .amb-venv
python -c "import os; from pathlib import Path; print((Path('.amb-venv') / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')).absolute())"
```

Use the printed interpreter as `<venv-python>`:

```text
<venv-python> -m pip install agent-memory-bridge==0.36.0
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

## 4. Host-specific places to look

These are operator hints, not generated adapters. Confirm the current host docs before editing.

| Host | Where the operator usually puts a stdio server | Notes |
|---|---|---|
| Generic JSON MCP client | `mcpServers.agentMemoryBridge` as above | Match the host's actual key if it differs. |
| Codex | User or project MCP config under the Codex home, table-shaped rather than JSON | v0.36 does not read or write `~/.codex`. Set `AGENT_MEMORY_BRIDGE_HOME` explicitly if the old database is `~/.codex/mem-bridge`. |
| OpenCode | User or project OpenCode MCP config with `command`, `args`, and `env` | Reload the runtime after editing. |
| Claude Desktop | The desktop app's MCP server config | Restart the app. Name the server `agentMemoryBridge`. |
| Cursor | The editor's MCP server config | Restart or reload MCP. Do not use a remote URL for this recipe. |

Do not claim any of these clients has been certified by installing the package.

## 5. Dockerized stdio, only if the host runs Docker locally

```bash
docker run --rm -i \
  -e AGENT_MEMORY_BRIDGE_HOME=/data/agent-memory-bridge \
  -e AGENT_MEMORY_BRIDGE_DEFAULT_SOURCE_CLIENT=generic \
  -e AGENT_MEMORY_BRIDGE_DEFAULT_CLIENT_TRANSPORT=stdio \
  -v /absolute/path/to/bridge-home:/data/agent-memory-bridge \
  ghcr.io/zzhang82/agent-memory-bridge:0.36.0 \
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
