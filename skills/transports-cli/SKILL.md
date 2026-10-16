---
name: nitrostack-python-transports-cli
description: Running a NitroStack Python server — stdio/http/dual transports, protocol era, and the nitrostack-py CLI (dev, generate, upgrade, pack, register).
---

## When to Use

Starting, deploying or connecting a Python NitroStack server, choosing a transport, or running `nitrostack-py` commands.

## Transports

Chosen by `MCP_TRANSPORT_TYPE` (or `ServerConfig(transport_type=...)`):

- `stdio` (default outside production): desktop clients such as Claude Desktop and Cursor launch the process.
- `http`: Streamable HTTP on `PORT`. Endpoints: `POST/GET/DELETE /mcp` (no trailing slash needed), legacy `GET /sse` + `POST /mcp/messages/`, `GET /mcp/health`, and a docs page at `GET /`.
- `dual` (default when `NODE_ENV=production`): stdio and HTTP in one process, sharing the same singletons.

Under stdio, stdout carries the protocol. Log through `context.logger`, never `print()`.

```python
from nitrostack import mcp_app, ServerConfig
from app_module import AppModule

@mcp_app(
    module=AppModule,
    server=ServerConfig(name="my-server", version="1.0.0", transport_type="http", max_sessions=100),
)
class App:
    pass
```

Protocol era: `MCP_STATELESS=true` forces stateless HTTP (MCP Inspector), `false` forces sessions. Otherwise `NITRO_MCP_PROTOCOL_VERSION` (`auto` default, `modern`, `legacy`), then `ServerConfig.protocol_era`.

## CLI

| Command | Does |
|---|---|
| `nitrostack-py init <name> --template python-starter\|python-pizzaz\|python-oauth` | New project, dependencies, widgets, agent skills |
| `nitrostack-py dev` | Hot-reload server (plus `src/widgets` dev server when present) |
| `nitrostack-py start` | Production server |
| `nitrostack-py generate tool\|module\|guard\|pipe\|interceptor\|filter\|service <name>` | Boilerplate |
| `nitrostack-py install [--production]` | Install dependencies (`uv sync` when uv is on PATH) |
| `nitrostack-py upgrade [--version X.Y.Z] [--dry-run]` | Move the project to another SDK release (replaces `vendor/nitrostack` from 0.4.2), and refresh agent skills |
| `nitrostack-py validate` | Check dependencies, `@mcp_app` imports and `@module()` references |
| `nitrostack-py pack [--dry-run]` | Build a wheel in `dist/` (never includes `.env`) |
| `nitrostack-py register --name <server> --file main.py` | Add the server to Claude Desktop's config |

If `nitrostack-py` is not on PATH, use `python -m nitrostack.cli.main <command>`.

## Do not

- Write to stdout in a stdio server.
- Add a trailing slash to the Streamable HTTP URL in client configs (`http://localhost:3000/mcp`).
- Edit files under `vendor/nitrostack`: that is the SDK copy the project runs, replaced wholesale when re-vendored.
