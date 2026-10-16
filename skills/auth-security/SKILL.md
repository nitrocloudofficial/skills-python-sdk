---
name: nitrostack-python-auth-security
description: API keys, JWT, OAuth 2.1 (OAuthModule, OAuthGuard), and scope checks in NitroStack Python MCP servers.
---

## When to Use

Protecting Python NitroStack tools: API keys, JWTs, or OAuth 2.1 (oauth template, Auth0/introspection). Not the TypeScript `OAuthModule` Nest package.

## Pick a module and guard

Import the module in the root `AppModule`, then guard tools. Guards fill `context.auth` (`subject`, `scopes`, `client_id`, `aud`, `claims`).

| Module | Guard | Configured by |
|---|---|---|
| `ApiKeyModule.for_root(keys_env_prefix="API_KEY", hashed=False)` | `ApiKeyGuard` | `x-api-key` header checked against `API_KEY`, `API_KEY_1`, `API_KEY_2`, ... (SHA-256 hashes when `hashed=True`) |
| `JWTModule.for_root(secret_env_var="JWT_SECRET", audience=..., issuer=...)` | `JwtGuard` | `Authorization: Bearer <jwt>` |
| `OAuthModule.for_root(resource_uri=..., authorization_servers=[...], ...)` | `OAuthGuard` | OAuth 2.1 access tokens, audience-bound |

## Wire OAuth on the root module

The `python-oauth` template imports `OAuthModule.for_root(...)` next to `ConfigModule` and the feature module. Values come from `.env` (`RESOURCE_URI`, `AUTH_SERVER_URL`, introspection client, audience, issuer). Follow `OAUTH_SETUP.md` in the generated project. Use `jwks_uri=...` instead of the introspection settings to verify JWT access tokens locally.

```python
import os
from nitrostack import module, ConfigModule, OAuthModule
from modules.flights.flights_module import FlightsModule
from health.system_health import SystemHealthCheck

@module(
    name="app",
    imports=[
        ConfigModule.for_root(env_file_path=".env", defaults={"PORT": "3000"}),
        OAuthModule.for_root(
            resource_uri=os.environ.get("RESOURCE_URI", "https://mcplocal"),
            authorization_servers=[os.environ.get("AUTH_SERVER_URL", "")],
            scopes_supported=["read", "write", "admin"],
            token_introspection_endpoint=os.environ.get("INTROSPECTION_ENDPOINT"),
            token_introspection_client_id=os.environ.get("INTROSPECTION_CLIENT_ID"),
            token_introspection_client_secret=os.environ.get("INTROSPECTION_CLIENT_SECRET"),
            audience=os.environ.get("TOKEN_AUDIENCE"),
            issuer=os.environ.get("TOKEN_ISSUER"),
        ),
        FlightsModule,
    ],
    providers=[SystemHealthCheck],
)
class AppModule:
    pass
```

## Protect tools

```python
from pydantic import BaseModel
from nitrostack import injectable, tool, use_guards, require_scopes, OAuthGuard, ExecutionContext
from guards.oauth_guard import create_scope_guard  # in the oauth template

class SearchInput(BaseModel):
    origin: str
    destination: str

@injectable()
class FlightsTools:
    @tool(name="search_flights", description="Search flights", input_schema=SearchInput)
    @use_guards(OAuthGuard, create_scope_guard(["read"]))
    async def search_flights(self, input: SearchInput, context: ExecutionContext) -> dict:
        return {"offers": []}

    @tool(name="cancel_order", description="Cancel an order", input_schema=SearchInput)
    @use_guards(OAuthGuard)
    @require_scopes("admin")
    async def cancel_order(self, input: SearchInput, context: ExecutionContext) -> dict:
        return {"cancelled": True}
```

`OAuthGuard`:

- Reads the Bearer token from metadata/headers (HTTP `Authorization` is forwarded into execution metadata).
- If **no token** and `OAUTH_REQUIRED` is not true: allow (local Studio/Inspector).
- If **no token** and `OAUTH_REQUIRED=true`: `PermissionError`.
- If a token is present: validate it with `OAuthService`, then populate `context.auth` (`aud` is a list).

Two scope checks behave differently without a token:

- The template's `create_scope_guard(["read"])` no-ops when OAuth is not required, so local calls still work.
- `require_scopes(...)` always needs `context.auth`: with no token it fails with "Not authenticated", even when `OAUTH_REQUIRED` is unset.

Inside a tool, `has_scope`, `has_any_scope` and `has_all_scopes` check `context.auth`. PKCE (`generate_pkce_params`), client ID metadata documents and `generate_www_authenticate_header` are exported for custom flows.

## Do not

- Copy TypeScript `OAuthGuard` / Passport strategies.
- Check `"aud" in context.auth.aud` assuming `aud` is a string. It is normalized to a list.
- Use `ApiKeyGuard` without `ApiKeyModule.for_root()` or an `API_KEY` variable: it then allows every call.
- Put secrets in skill files or commit `.env`.
