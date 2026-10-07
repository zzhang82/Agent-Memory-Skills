# Verification and repair

Verify in three layers. Passing an earlier layer does not pass a later one.

| Layer | Proves | Does not prove |
|---|---|---|
| Server `doctor` / `verify` | The selected install or remote MCP endpoint can answer. | The host loaded its config. |
| Client tool list | The restarted host sees the expected AMB tools. | A later session can recall a real memory. |
| Two-session first win | Session B recovered session A's explicit memory through AMB. | Vendor certification, ranking quality, or automatic learning. |

## Server

Local stdio:

```text
<venv-python> -m agent_mem_bridge doctor
<venv-python> -m agent_mem_bridge verify
```

Remote Streamable HTTP:

```text
agent-memory-bridge doctor --url https://amb.example.test/mcp --token-file /private/amb/http-token --json
agent-memory-bridge verify --url https://amb.example.test/mcp --token-file /private/amb/http-token --json
```

Remote probes are read-only. They must not open a local database when the URL fails. `/healthz` and `/readyz` are only process and readiness checks.

Optional local depth, not part of the connection gate:

```text
<venv-python> -m agent_mem_bridge index-health
<venv-python> -m agent_mem_bridge db-health
```

## Client tool visibility

Restart or reload the host after config edits. In the host, list the `agentMemoryBridge` tools.

- Everyday expects `recall`, `browse`, `stats`, `store`, `revise`, `annotate`.
- Full expects all 17 tools and no 18th tool.
- If the list is empty, stop. Do not use `project init`, Explore, or Inspect as a substitute for MCP registration.
- If extra tools are visible, the server is still the full surface. Fix the client allowlist or narrow the instruction. Do not claim the extra tools are unauthorized at the server.

## Two-session first win

Use one non-secret decision the operator actually wants remembered.

Session A, through the host's MCP tool call, not a shell alias:

```text
store(
  namespace="project:<name>",
  kind="memory",
  content="record_type: decision\nclaim: Merge pull requests only after CI is green on the target branch.\nreason: Broken main blocked two releases this month.\nscope: project:<name>\nconfidence: observed"
)
```

Record the returned memory id. End session A completely.

Session B must be a new session with the same host registration and the same authority. Ask a project question, for example "What is required before we merge a pull request?" Pass only if `recall` returns that memory and the answer uses it.

Fail if session B only repeats session A's transcript, only shows CLI `explore` or `inspect`, or cannot attribute the answer to AMB. If no live second session was opened, the result is NOT RUN, not PASS.

The same test works over HTTP when both sessions use the same `/mcp` URL and token. Do not run the write against production as a casual probe.

## Repair

| Symptom | What to check | Repair |
|---|---|---|
| Host lists no AMB tools | Wrong config file, stale process, bad command path | Fix the host entry, restart, recheck the tool list. |
| `doctor` warns about missing `config.toml` | Optional config path | Continue if the baseline server runs. Add config only for a real setting. |
| v0.36 cannot see old memory | Default home is `~/.local/share/agent-memory-bridge`; `~/.codex/mem-bridge` is no longer opened automatically | Set `AGENT_MEMORY_BRIDGE_HOME` to the old directory, or stop AMB and copy it to the neutral home. Do not delete the old directory. |
| Remote URL fails and a local database answers | Forbidden fallback | Remove the local fallback. Keep `AGENT_MEMORY_BRIDGE_AUTHORITY_URL` and fail closed. |
| HTTP 401 or token error | Token file mode, wrong file, or header not sent | Mode `0600`, regular file, `Authorization: Bearer`. Do not print the token. |
| Non-loopback server exits immediately | Missing token or allowlists | Set token file, allowed hosts, and allowed origins. Do not bind wildcard without them. |
| Capture wrote nothing on a remote hook | Expected v0.36 boundary | Keep capture on a local authority only. Remote recall can remain enabled. |
| Two clients recall different memories | Different homes or URLs | Point both at one `AGENT_MEMORY_BRIDGE_HOME` or one authority URL. |
| Need to destroy or unbind data | Operator intent | Stop. Confirm explicitly before `unbind-repo`, restore, or volume deletion. |

Do not repair a failed remote authority by creating a fresh local database and calling it the same project.
