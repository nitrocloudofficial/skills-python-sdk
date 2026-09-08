---
name: nitrostack-python-auth-security
description: OAuth 2.1, OAuthModule, OAuthGuard, and scope guards in NitroStack Python MCP servers.
---

## When to Use

Protecting Python NitroStack tools (oauth template, Auth0/introspection). Not the TypeScript `OAuthModule` Nest package.

## Wire OAuth on the root module

The `python-oauth` template imports `OAuthModule.for_root(...)` next to `ConfigModule` and the feature module. Values come from `.env` (`RESOURCE_URI`, `AUTH_SERVER_URL`, introspection client, audience, issuer). Follow `OAUTH_SETUP.md` in the generated project.

```python
from nitrostack import module, ConfigModule, OAuthModule
import os

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
from nitrostack import use_guards, OAuthGuard
from guards.oauth_guard import create_scope_guard

@use_guards(OAuthGuard, create_scope_guard(["read"]))
```

`OAuthGuard`:

- Reads Bearer token from metadata/headers (HTTP `Authorization` is forwarded into execution metadata).
- If **no token** and `OAUTH_REQUIRED` is not true → allow (local Studio/Inspector).
- If **no token** and `OAUTH_REQUIRED=true` → `PermissionError`.
- If token present → `OAuthService.introspect_token`; populate `context.auth` (`subject`, `scopes`, `aud` as a list, claims).

`create_scope_guard(["read"])` no-ops when oauth is not required; otherwise requires those scopes on `context.auth.scopes`.

## Do not

- Copy TypeScript `OAuthGuard` / Passport strategies.
- Check `"aud" in context.auth.aud` assuming `aud` is a string — it is normalized to a list.
- Put secrets in skill files or commit `.env`.
