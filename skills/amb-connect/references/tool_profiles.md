# Tool profiles

AMB v0.36 always serves the same 17 public MCP tools on stdio and Streamable HTTP. A profile is a client-side exposure choice. It does not remove tools from the server, create an ACL, or make a bearer token partial.

If the host cannot filter tools, leave the server unchanged and instruct the agent which profile is in scope. Say clearly that this is guidance, not enforcement.

Public order:

1. `store`
2. `recall`
3. `browse`
4. `stats`
5. `forget`
6. `feedback`
7. `promote`
8. `annotate`
9. `revise`
10. `export`
11. `begin_run`
12. `record_run_event`
13. `get_run`
14. `complete_run`
15. `claim_signal`
16. `extend_signal_lease`
17. `ack_signal`

There is no MCP tool #18. Knowledge Explorer, `project`, `doctor`, `verify`, `inspect`, `explore`, and `lifecycle-hook` are CLI commands, not MCP tools.

## Profiles

| Profile | Tools | Use |
|---|---|---|
| Everyday (6) | `recall`, `browse`, `stats`, `store`, `revise`, `annotate` | Normal project memory. Default for a new host. |
| Read-only (3) | `recall`, `browse`, `stats` | Inspection without client-side writes. |
| Tracked Work (+4) | Everyday plus `begin_run`, `record_run_event`, `get_run`, `complete_run` | Explicit episode evidence. |
| Signals (+3) | Everyday plus `claim_signal`, `extend_signal_lease`, `ack_signal` | Lightweight coordination. |
| Full (17) | All public tools | Maintenance, export, revision, runs, and signals. |
| Custom | Operator-listed subset | Only when a named profile does not fit. |

`export` can reveal a whole namespace. Keep it out of Everyday. `forget`, `promote`, and `feedback` are specialized maintenance or evaluation tools; use them deliberately.

Tracked Work and Signals stack on Everyday. They do not include each other unless the operator asks for both.

## Client configuration

Prefer the host's real allowlist key. Examples below are generic patterns, not a promise that a named client accepts them.

JSON hosts that support an enabled-tools list:

```json
{
  "mcpServers": {
    "agentMemoryBridge": {
      "command": "<venv-python>",
      "args": ["-m", "agent_mem_bridge"],
      "env": {
        "AGENT_MEMORY_BRIDGE_HOME": "/absolute/path/to/shared-bridge-home"
      },
      "enabledTools": ["recall", "browse", "stats", "store", "revise", "annotate"]
    }
  }
}
```

For HTTP, use the same tool list on the URL-shaped server entry from [remote_http_recipe.md](remote_http_recipe.md).

Hosts that use approval prompts instead of allowlists:

- Everyday writes: approve `store`, `revise`, and `annotate` as mutating calls.
- Read-only: approve only `recall`, `browse`, and `stats`; deny mutating calls in the host policy if it has one.
- Full: do not enable automatic approval for `export`, `forget`, `revise`, or run completion.

Hosts with neither allowlists nor approvals:

```text
AMB profile for this session: Everyday.
You may call recall, browse, stats, store, revise, and annotate.
Do not call export, forget, feedback, promote, run tools, or signal tools unless the operator switches profile.
This instruction is not a server authorization boundary.
```

## Security boundary

- Client allowlists, hidden tool lists, and system instructions affect only that client.
- Another client with the same home or the same bearer token can call all 17 tools.
- The HTTP token is not narrowed by profile.
- `hardened-local` is still a cooperative local profile, not per-namespace authorization.
- Provenance fields such as `source_client` are caller-declared. They do not prove who called the tool.
