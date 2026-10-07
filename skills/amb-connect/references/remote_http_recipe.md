# Remote HTTP recipe

Use this when clients cannot launch a local AMB process, or when several machines must share one authority. The database stays on local disk on the authority host. Clients speak MCP Streamable HTTP to `/mcp`.

## 1. Confirm the endpoint

A local rehearsal on the authority host:

```text
agent-memory-bridge serve --transport streamable-http
agent-memory-bridge doctor --url http://127.0.0.1:8000/mcp --json
agent-memory-bridge verify --url http://127.0.0.1:8000/mcp --json
```

The default listener is loopback. `--url` probes do not open a fallback local database and do not write a diagnostic memory.

For a non-loopback process, start with a token file and explicit allowlists:

```text
agent-memory-bridge serve --transport streamable-http \
  --host 127.0.0.1 \
  --port 8000 \
  --token-file /private/amb/http-token \
  --allowed-host localhost:8000 \
  --allowed-host 127.0.0.1:8000 \
  --allowed-origin http://localhost:8000 \
  --allowed-origin http://127.0.0.1:8000
```

Prefer publishing through the official Compose file in [docker_deployment.md](docker_deployment.md). Reach it from another machine through TLS or an authenticated tunnel. Change allowed hosts and origins to the externally presented values, not a wildcard.

## 2. Generic remote client

The MCP URL is the `/mcp` path. Health URLs are not the MCP URL.

```json
{
  "mcpServers": {
    "agentMemoryBridge": {
      "url": "https://amb.example.test/mcp",
      "headers": {
        "Authorization": "Bearer ${AMB_HTTP_TOKEN}"
      }
    }
  }
}
```

Replace the placeholder URL with the tunnel or reverse-proxy URL the operator actually exposes. Put the token in the host's secret store. Do not paste it into a repository, chat log, or process list.

If the host cannot expand environment variables inside headers, use its secret reference. If it cannot send `Authorization` at all, stop. Do not switch that client to an unauthenticated listener.

For lifecycle recall from a host that also has the CLI, point the hook process at the same authority:

```text
AGENT_MEMORY_BRIDGE_AUTHORITY_URL=https://amb.example.test/mcp
AGENT_MEMORY_BRIDGE_HTTP_TOKEN_FILE=/private/amb/http-token
```

That selection is HTTP-only. A failed remote call must not open a local database.

## 3. Where this shape usually goes

| Client | What to set | What not to do |
|---|---|---|
| Generic MCP client | Remote server URL plus bearer header | Do not also set `command` unless the host uses a local proxy process. |
| Bot or hosted runtime | Its MCP HTTP connection and secret header | Do not mount the NAS database into the bot. |
| Remote server agent | Same URL and token as the other clients | Do not create a second home on that server. |
| Local coding client that can do either transport | Use HTTP only when it should share the remote authority | Do not keep a separate local home for the same project. |

v0.36 has no per-client remote installer. The operator maps this shape onto the host.

## 4. Checks that are not connection proof

```text
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/readyz
```

`/healthz` means the process is up. `/readyz` means the authority database and expected schema are ready enough for a bounded check. Neither lists tools or returns memory.

Then run remote `doctor` and `verify` with `--url` and `--token-file`. After that, the host's own tool list is the registration gate.

## 5. Failure behavior

- If the authority is down, the client gets a transport failure. Do not configure a local fallback writer.
- A write can commit even when the response is lost. Retry an identical `store` using duplicate-safe content. Run and event retries need their existing idempotency keys. Do not blindly retry every tool.
- Do not target production with candidate acceptance scripts. Isolated copies only.
