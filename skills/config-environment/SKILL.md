---
name: nitrostack-python-config-environment
description: Settings in NitroStack Python — ConfigModule, ConfigService, .env precedence, and the environment variables the SDK reads.
---

## When to Use

Reading settings or secrets, editing `.env`, or debugging a server that picks up the wrong port, name or transport.

## Precedence

Highest first:

1. The process environment (shell, NitroStudio, Docker, CI).
2. The project's `.env`.
3. `ConfigModule.for_root(defaults={...})`.

`.env` never overwrites a variable that is already set (nitrostack 0.4.1 and later). NitroStudio starts each project with its own `PORT`, so several servers can run side by side even though `.env` says `PORT=3000`. On older SDKs `.env` won. Projects run the SDK copy in `vendor/nitrostack`, so check its version (`vendor/nitrostack/pyproject.toml`) when `.env` seems to override the environment, then run `nitrostack-py upgrade` and `nitrostack-py install`. If `upgrade` fails with "Refusing to write an invalid pyproject.toml", the CLI is older than 0.4.2: run `uvx --from nitrostack nitrostack-py upgrade`.

## Read settings with ConfigService

```python
from nitrostack import ConfigModule, ConfigService, injectable, module

@injectable(deps=[ConfigService])
class WeatherService:
    def __init__(self, config: ConfigService):
        self.units = config.get("WEATHER_UNITS", "metric")
        self.api_key = config.get_or_throw("WEATHER_API_KEY")  # KeyError if unset

@module(
    name="app",
    imports=[ConfigModule.for_root(env_file_path=".env", defaults={"WEATHER_UNITS": "metric"})],
    providers=[WeatherService],
)
class AppModule:
    pass
```

Inject `ConfigService` rather than reading `os.environ` in services: it applies the precedence above and the module defaults.

## Variables the SDK reads

| Variable | Meaning |
|---|---|
| `PORT` / `MCP_SERVER_PORT` | HTTP port (default 3000). Studio sets it; don't hard-code a port in code. |
| `HOST` | Bind address (default `127.0.0.1`; `0.0.0.0` in containers). |
| `SERVER_NAME` / `SERVER_DESC` | Name and description clients show. `init` sets `SERVER_NAME` to the folder name. |
| `MCP_TRANSPORT_TYPE` | `stdio`, `http` or `dual` (transports-cli skill). |
| `MCP_STATELESS` | `true` for stateless HTTP (MCP Inspector). |
| `NITROSTACK_APP_MODE` | Widget metadata: `universal` (default), `openai`, `mcp-app`. |
| `WIDGETS_DEV_PORT` | Port of the optional `src/widgets` dev server (default 3001). |
| `OAUTH_REQUIRED` | `true` makes `OAuthGuard` reject calls without a token. |
| `API_KEY`, `API_KEY_1`, ... | Keys for `ApiKeyModule` / `ApiKeyGuard`. |
| `NITROSTACK_LOG_LEVEL` / `NITROSTACK_LOG_FILE` | Logging (default file `nitrostack.log`). |
| `NITROSTACK_HTTP_DEBUG` | `1` logs every HTTP request to stderr. |

## Do not

- Commit `.env` or put secrets in code. Add new keys to `.env.example` with placeholder values.
- Remove `PORT` handling or bind a fixed port in `main.py`.
- Print `ConfigService` values that hold secrets to the log.
