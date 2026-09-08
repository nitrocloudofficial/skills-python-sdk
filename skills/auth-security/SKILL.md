---
name: nitrostack-python-auth-security
description: Best practices for implementing JWT, API Keys, OAuth 2.1, RBAC, and Scope Guards in NitroStack Python MCP servers.
---

## When to Use
Use this skill when configuring security modules, implementing user authentication, protecting Python tools/resources with guards, verifying JWTs or API keys, or securing endpoints with OAuth 2.1 and PKCE.

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
            secret_env_var="JWT_SECRET",  # Reads secret from os.environ["JWT_SECRET"]
            expires_in="24h",             # Token expiration window (e.g., '1h', '24h', '7d')
            audience=os.environ.get("TOKEN_AUDIENCE"),
            issuer=os.environ.get("TOKEN_ISSUER"),
        ),
        UserModule,
    ],
)
class AppModule:
    pass
```

### Protect Tools with `JwtGuard`:
`JwtGuard` automatically extracts the `Bearer <token>` from metadata/headers, verifies the signature, and populates `context.auth` (`AuthContext` containing `subject`, `scopes`, `client_id`, `claims`, etc.).

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

## 2. API Key Authentication

Use `ApiKeyModule` for service-to-service validation.

### Register `ApiKeyModule`:
```python
from nitrostack import module, ApiKeyModule

@module(
    name="app",
    imports=[
        ApiKeyModule.for_root(
            keys_env_prefix="API_KEY",  # Reads API_KEY, API_KEY_1, API_KEY_2, etc.
            header_name="x-api-key",    # Header to inspect in request metadata
            hashed=False,               # Set True if stored keys are SHA-256 hashes
        ),
        SystemModule,
    ],
)
class AppModule:
    pass
```

### Protect Tools with `ApiKeyGuard`:
`ApiKeyGuard` checks for the API key in `context.metadata["x-api-key"]` or `context.metadata["headers"]["x-api-key"]` and validates it against `ApiKeyService`.

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

## 3. Role-Based Access Control (RBAC) & Custom Guards

Custom guards implement the `Guard` protocol with `async def can_activate(self, context: ExecutionContext) -> bool`. Chain authentication guards before authorization guards using `@use_guards(...)`.

```python
from nitrostack import injectable, tool, use_guards, JwtGuard, ExecutionContext
from pydantic import BaseModel

@injectable()
class AdminGuard:
    async def can_activate(self, context: ExecutionContext) -> bool:
        # Requires JwtGuard / OAuthGuard to have populated context.auth first
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
    @use_guards(JwtGuard, AdminGuard)  # First authenticate with JWT, then check Admin role
    async def reset_database(self, input: ResetDbInput, context: ExecutionContext) -> dict:
        return {"success": True, "initiated_by": context.auth.subject}
```

---

## 4. OAuth 2.1 & Scopes

Use `OAuthModule` for OAuth 2.1 protected resource metadata discovery and token introspection.

### Wire `OAuthModule` on `AppModule`:
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
)
class AppModule:
    pass
```

### Scope Protection with `require_scopes` or Custom Scope Guards:
```python
from nitrostack import injectable, tool, use_guards, OAuthGuard, require_scopes, ExecutionContext
from pydantic import BaseModel

class FlightSearchInput(BaseModel):
    origin: str
    destination: str

@injectable()
class FlightTools:
    @tool(
        name="search_flights",
        description="Search available flights",
        input_schema=FlightSearchInput,
    )
    @use_guards(OAuthGuard)
    @require_scopes("read")
    async def search_flights(self, input: FlightSearchInput, context: ExecutionContext) -> dict:
        return {"flights": []}
```

### Behavior of `OAuthGuard`:
- Reads Bearer token from `context.metadata` (`authorization`, `headers`, or `_oauth`).
- If **no token** and `OAUTH_REQUIRED` is not `true` → allows the call (useful for local development in Studio/Inspector).
- If **no token** and `OAUTH_REQUIRED=true` → raises `PermissionError`.
- If token present → validates token via `OAuthService.introspect_token` and populates `context.auth` (`subject`, `scopes`, `aud` as a normalized `list`, `claims`).

---

## 5. Scope & PKCE Utility Functions

NitroStack provides built-in helper functions in `nitrostack`:
- `has_scope(context.auth, "read")` -> `bool`
- `has_all_scopes(context.auth, ["read", "write"])` -> `bool`
- `has_any_scope(context.auth, ["admin", "write"])` -> `bool`
- `generate_code_verifier()`, `generate_code_challenge(verifier)`, `verify_pkce(verifier, challenge)`

---

## Do Not
- Do not copy TypeScript `@nitrostack/core` decorator syntax or Passport strategies.
- Do not assume `context.auth.aud` is a string; NitroStack normalizes `aud` to a `list` to ensure safe membership checks (`"aud" in context.auth.aud`).
- Do not commit `.env` or hardcode secrets into source files.
