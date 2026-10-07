# Transports and auth

AMB v0.36 has two transports and one public tool surface. Both serve the same 17 MCP tools. There is no third HTTP API.

| Transport | Who speaks | Authority data | When to use |
|---|---|---|---|
| stdio | Host launches `<venv-python> -m agent_mem_bridge`. JSON-RPC on stdin/stdout. | Local SQLite/WAL under `AGENT_MEMORY_BRIDGE_HOME`. | Host and database are on the same trusted machine. |
| Streamable HTTP | Host connects to `<authority>/mcp` with the MCP Streamable HTTP client. | One server or NAS owns the SQLite/WAL files on local disk. | Clients are remote. They must not mount the database. |

No-argument `agent-memory-bridge`, and `serve --transport stdio`, stay on stdio. HTTP starts only with `serve --transport streamable-http`.

## Selection order

1. If a local home already holds the project memory, point every sharing client at that same `AGENT_MEMORY_BRIDGE_HOME`.
2. If a remote authority URL already exists, point every sharing client at that same URL. Do not also open a local database for those clients.
3. Otherwise create one new local virtualenv home, or one new Docker authority. Do not create both for the same project unless the operator is deliberately running an isolated rehearsal.

An explicit `AGENT_MEMORY_BRIDGE_AUTHORITY_URL` selects HTTP on the lifecycle-hook path before any local database inspection. (Note that remote `doctor` and `verify` CLI probes select HTTP via their explicit `--url` CLI argument, and host MCP client configurations specify stdio or HTTP at the host transport layer). If the remote authority URL fails on the lifecycle path, the hook call fails closed. It is not an empty recall and not permission to open `bridge.db` locally.

## Environment

| Variable | Role |
|---|---|
| `AGENT_MEMORY_BRIDGE_HOME` | Root for the SQLite database, logs, and local lifecycle evidence. Default `~/.local/share/agent-memory-bridge`. |
| `AGENT_MEMORY_BRIDGE_CONFIG` | Optional `config.toml`. Default location is `~/.config/agent-memory-bridge/config.toml`. Absence is a warning, not a failed install. |
| `AGENT_MEMORY_BRIDGE_AUTHORITY_URL` | Remote Streamable HTTP MCP URL, including the `/mcp` path. When set, lifecycle recall does not open a local database. |
| `AGENT_MEMORY_BRIDGE_HTTP_TOKEN_FILE` | Path to the bearer file. The token is never passed as a CLI argument or URL. |
| `AGENT_MEMORY_BRIDGE_HTTP_HOST` | Bind address. Default `127.0.0.1`. |
| `AGENT_MEMORY_BRIDGE_HTTP_PORT` | Bind port. Default `8000`. |
| `AGENT_MEMORY_BRIDGE_HTTP_ALLOWED_HOSTS` | Comma-separated Host allowlist. Required for a non-loopback bind. |
| `AGENT_MEMORY_BRIDGE_HTTP_ALLOWED_ORIGINS` | Comma-separated Origin allowlist. Required for a non-loopback bind. |
| `AGENT_MEMORY_BRIDGE_DEFAULT_SOURCE_CLIENT` | Optional caller-declared provenance label. Not authenticated identity. |
| `AGENT_MEMORY_BRIDGE_DEFAULT_CLIENT_TRANSPORT` | Optional provenance label such as `stdio`. |
| `AGENT_MEMORY_BRIDGE_OPERATING_PROFILE` | `local-single-user` or `hardened-local`. Neither is OAuth or a per-namespace ACL. |

v0.36 does not open `~/.codex/mem-bridge` by itself. To keep using that directory, set `AGENT_MEMORY_BRIDGE_HOME` to it, or stop AMB and copy the directory to the neutral home. AMB does not migrate or delete the old directory.

## Bearer token file

Create the token outside the git checkout and outside the database volume:

```bash
umask 077
install -d -m 0700 /private/amb
openssl rand -base64 32 > /private/amb/http-token
chmod 0600 /private/amb/http-token
```

Rules:

- Mode `0600`, regular file, not a symlink, not group or world readable. AMB rejects a POSIX mode with group or world bits.
- One dedicated token per authority. Do not reuse another service's token.
- The token grants the entire tool surface, including mutation and export. It is not scoped by namespace.
- Clients send `Authorization: Bearer <token>` on the MCP HTTP request. Do not log the header or file contents.
- This is MCP SDK bearer verification, not an OAuth authorization server. Clients that require OAuth discovery are not automatically compatible.
- Rotate by replacing the file and restarting during an approved maintenance window.

## Host, origin, and network

- Loopback can use the built-in localhost allowlists.
- A non-loopback bind requires the token file plus explicit allowed hosts and origins. Startup fails closed without them.
- Host and Origin checks are not TLS and not identity. Requests with an invalid Origin are rejected. A missing Origin can be a valid native MCP request.
- Do not send the bearer token over plaintext on an untrusted LAN or the internet. Use TLS or an authenticated SSH or overlay tunnel.
- Do not leave a direct bypass around an authenticating reverse proxy.
- Do not publish a wildcard unauthenticated listener.

## What is not a transport

- `POST /store`, `GET /recall`, or any other invented REST path.
- `/healthz` and `/readyz`. They report process and bounded readiness only. They contain no memory and do not replace MCP.
- NFS, SMB, or a synced folder as a multi-writer database. SQLite/WAL stays on a local filesystem of the authority host.
