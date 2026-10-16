---
name: nitrostack-python-auth-security
description: API keys, JWT, OAuth 2.1 (OAuthModule, OAuthGuard), and scope checks in NitroStack Python MCP servers.
---

## When to Use

Protecting Python NitroStack tools with API keys, JWTs, or OAuth 2.1 (oauth template, Auth0/introspection). Not the TypeScript `OAuthModule` Nest package.

## Pick a module and guard

Import the module in the root `AppModule`, then guard tools. Guards fill `context.auth` (`subject`, `scopes`, `client_id`, `aud`, `claims`).

| Module | Guard | Configured by |
|---|---|---|
| `ApiKeyModule.for_root(keys_env_prefix="API_KEY", hashed=False)` | `ApiKeyGuard` | `x-api-key` header checked against `API_KEY`, `API_KEY_1`, `API_KEY_2`, ... (SHA-256 hashes when `hashed=True`) |
| `JWTModule.for_root(secret_env_var="JWT_SECRET", audience=..., issuer=...)` | `JwtGuard` | `Authorization: Bearer <jwt>` |
| `OAuthModule.for_root(resource_uri=..., authorization_servers=[...], ...)` | `OAuthGuard` | OAuth 2.1 access tokens, audience-bound |

---

## 1. JSON Web Tokens (JWT)

Use `JWTModule` for stateless token-based authentication.

### Register `JWTModule` on `AppModule`:

```python
from nitrostack import module, ConfigModule, JWTModule
import os

@module(
    name="app",
    imports=[
        ConfigModule.for_root(env_file_path=".env"),
        JWTModule.for_root(
            secret_env_var="JWT_SECRET",
            expires_in="24h",
            audience=os.environ.get("TOKEN_AUDIENCE"),
            issuer=os.environ.get("TOKEN_ISSUER"),
        ),
        UserModule,
    ],
)
class AppModule:
    pass
```

### Protect tools with `JwtGuard`:

`JwtGuard` extracts `Bearer <token>` from metadata/headers, verifies the signature, and populates `context.auth`.

```python
from nitrostack import injectable, tool, use_guards, JwtGuard, ExecutionContext
from pydantic import BaseModel, Field

class UserProfileInput(BaseModel):
    include_preferences: bool = Field(default=False)

@injectable()
class UserTools:
    @tool(
        name="get_my_profile",
        description="Fetch the authenticated user profile",
        input_schema=UserProfileInput,
    )
    @use_guards(JwtGuard)
    async def get_my_profile(self, input: UserProfileInput, context: ExecutionContext) -> dict:
        user_id = context.auth.subject
        roles = context.auth.claims.get("roles", [])
        return {"user_id": user_id, "roles": roles}
```

---

## 2. API key authentication

Use `ApiKeyModule` for service-to-service validation.

### Register `ApiKeyModule`:

```python
from nitrostack import module, ApiKeyModule

@module(
    name="app",
    imports=[
        ApiKeyModule.for_root(
            keys_env_prefix="API_KEY",
            header_name="x-api-key",
            hashed=False,
        ),
        SystemModule,
    ],
)
class AppModule:
    pass
```

### Protect tools with `ApiKeyGuard`:

`ApiKeyGuard` checks `context.metadata["x-api-key"]` or `context.metadata["headers"]["x-api-key"]` and validates against `ApiKeyService`.

```python
from nitrostack import injectable, tool, use_guards, ApiKeyGuard, ExecutionContext
from pydantic import BaseModel

class MetricsInput(BaseModel):
    category: str

@injectable()
class SystemTools:
    @tool(
        name="fetch_system_metrics",
        description="Fetch internal system metrics (API Key required)",
        input_schema=MetricsInput,
    )
    @use_guards(ApiKeyGuard)
    async def fetch_metrics(self, input: MetricsInput, context: ExecutionContext) -> dict:
        return {"status": "ok", "cpu_load": 0.42}
```

---

## 3. RBAC and custom guards

Custom guards implement `async def can_activate(self, context: ExecutionContext) -> bool`. Chain authentication guards before authorization guards with `@use_guards(...)`.

```python
from nitrostack import injectable, tool, use_guards, JwtGuard, ExecutionContext
from pydantic import BaseModel

@injectable()
class AdminGuard:
    async def can_activate(self, context: ExecutionContext) -> bool:
        if not context.auth:
            return False
        return context.auth.claims.get("role") == "admin"

class ResetDbInput(BaseModel):
    confirm: bool

@injectable()
class AdminTools:
    @tool(
        name="reset_database",
        description="Wipes database. Admin only.",
        input_schema=ResetDbInput,
    )
    @use_guards(JwtGuard, AdminGuard)
    async def reset_database(self, input: ResetDbInput, context: ExecutionContext) -> dict:
        return {"success": True, "initiated_by": context.auth.subject}
```

---

## 4. OAuth 2.1 and scopes

Use `OAuthModule` for protected-resource metadata and token introspection (or `jwks_uri=...` for local JWT verification).

The `python-oauth` template wires `OAuthModule.for_root(...)` next to `ConfigModule`. Values come from `.env` (`RESOURCE_URI`, `AUTH_SERVER_URL`, introspection client, audience, issuer). Follow `OAUTH_SETUP.md` in the generated project.

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

### Protect tools with scopes:

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

### `OAuthGuard` behavior

- Reads the Bearer token from metadata/headers (HTTP `Authorization` is forwarded into execution metadata).
- If **no token** and `OAUTH_REQUIRED` is not `true`: allow (local Studio/Inspector).
- If **no token** and `OAUTH_REQUIRED=true`: `PermissionError`.
- If a token is present: validate via `OAuthService`, then populate `context.auth` (`aud` is a normalized `list`, not a string).

Two scope checks behave differently without a token:

- The template's `create_scope_guard(["read"])` no-ops when OAuth is not required, so local calls still work.
- `require_scopes(...)` always needs `context.auth`: with no token it fails with "Not authenticated", even when `OAUTH_REQUIRED` is unset.

---

## 5. Scope and PKCE helpers

Built-in helpers in `nitrostack`:

- `has_scope(context.auth, "read")` → `bool`
- `has_all_scopes(context.auth, ["read", "write"])` → `bool`
- `has_any_scope(context.auth, ["admin", "write"])` → `bool`
- `generate_code_verifier()`, `generate_code_challenge(verifier)`, `verify_pkce(verifier, challenge)`
- `generate_pkce_params()` for a full PKCE parameter set; `generate_www_authenticate_header` for custom flows

---

## Do not

- Copy TypeScript `@nitrostack/core` decorator syntax or Passport strategies.
- Assume `context.auth.aud` is a string; it is normalized to a `list` (`"aud" in context.auth.aud`).
- Use `ApiKeyGuard` without `ApiKeyModule.for_root()` or an `API_KEY` variable: it then allows every call.
- Commit `.env` or hardcode secrets into source files.
