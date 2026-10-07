# Docker deployment

Deploy one official AMB 0.36.0 authority with Compose. This is a new authority unless the operator explicitly mounts an existing local home. It is not a migration or a license to replace production.

## Official shape

The published image is `ghcr.io/zzhang82/agent-memory-bridge:0.36.0`. It runs `agent-memory-bridge serve --transport streamable-http` as UID/GID `10001`, exposes port `8000`, and uses `/readyz` as its health check.

Use the v0.36.0 `compose.yml` from the AMB source tag. The operational contract is:

```yaml
name: agent-memory-bridge

services:
  amb-mcp:
    image: ghcr.io/zzhang82/agent-memory-bridge:0.36.0
    user: "10001:10001"
    restart: unless-stopped
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    environment:
      AGENT_MEMORY_BRIDGE_HOME: /data/agent-memory-bridge
      AGENT_MEMORY_BRIDGE_OPERATING_PROFILE: hardened-local
      AGENT_MEMORY_BRIDGE_HTTP_HOST: 0.0.0.0
      AGENT_MEMORY_BRIDGE_HTTP_PORT: "8000"
      AGENT_MEMORY_BRIDGE_HTTP_TOKEN_FILE: /run/secrets/amb_http_token
      AGENT_MEMORY_BRIDGE_HTTP_ALLOWED_HOSTS: ${AMB_ALLOWED_HOSTS:-localhost:8000,127.0.0.1:8000}
      AGENT_MEMORY_BRIDGE_HTTP_ALLOWED_ORIGINS: ${AMB_ALLOWED_ORIGINS:-http://localhost:8000,http://127.0.0.1:8000}
    ports:
      - "127.0.0.1:${AMB_HTTP_PORT:-8000}:8000"
    volumes:
      - amb-home:/data/agent-memory-bridge
    secrets:
      - amb_http_token

volumes:
  amb-home:

secrets:
  amb_http_token:
    file: ${AMB_HTTP_TOKEN_FILE:?Set AMB_HTTP_TOKEN_FILE to a private host-local bearer file readable by UID 10001}
```

The process listens on all container interfaces. Compose still publishes `8000` to host loopback only. Token and Host/Origin checks remain required.

## Prepare the token

On the authority host, outside the checkout and outside the volume:

```bash
umask 077
install -d -m 0700 /private/amb
openssl rand -base64 32 > /private/amb/http-token
chmod 0600 /private/amb/http-token
```

The container user is UID `10001`. The file must be readable by that UID and must not grant group or world access. Export the host path only:

```bash
export AMB_HTTP_TOKEN_FILE=/private/amb/http-token
docker compose -f compose.yml up -d
```

Compose fails configuration when `AMB_HTTP_TOKEN_FILE` is missing. The token value is not an environment variable and not image metadata.

## Network

- Local clients use `http://127.0.0.1:8000/mcp`.
- Remote clients reach that loopback port through a protected tunnel or reverse proxy.
- If the published host port changes, set `AMB_ALLOWED_HOSTS` and `AMB_ALLOWED_ORIGINS` to the externally presented values.
- Do not remove the `127.0.0.1:` bind prefix to expose the container directly.
- Plain HTTP is only for loopback or an already protected transport.

## Volume rules

- The named `amb-home` volume holds the database, WAL, metadata, and local receipt secret.
- Do not run `docker compose down --volumes` against an authority.
- Replacing the container is not a restore and must not rotate the database epoch.
- Do not put this volume on an NFS or CIFS driver.
- A bind mount is allowed only when the operator replaces `amb-home:/data/agent-memory-bridge` with an explicit local host directory owned for UID/GID `10001`. The image will not chown arbitrary host data. Check the real filesystem with `findmnt -T` before startup.

## Optional service process

Basic MCP does not need the background service. If the operator enables it, run `agent-memory-bridge service` as a separate container or process with the same image and the same local volume. Do not start a second authority.

## After startup

From the host:

```text
agent-memory-bridge doctor --url http://127.0.0.1:8000/mcp --token-file /private/amb/http-token --json
agent-memory-bridge verify --url http://127.0.0.1:8000/mcp --token-file /private/amb/http-token --json
```

Then connect clients with [remote_http_recipe.md](remote_http_recipe.md).
