---
name: nitrostack-python-middleware-pipeline
description: Guards, middleware, interceptors, pipes, and exception filters on NitroStack Python tools.
---

## When to Use

Authorizing or transforming a tool/resource/prompt call in the **Python** SDK (`nitrostack.core.pipeline`).

## Stacking on a handler

Decorators attach lists on the function: `_mcp_guards`, `_mcp_middleware`, `_mcp_interceptors`, `_mcp_pipes`, `_mcp_filters`.

```python
from nitrostack import tool, use_guards, OAuthGuard, ExecutionContext
from guards.oauth_guard import create_scope_guard

@tool(name="search_flights", description="...", input_schema=SearchFlightsInput)
@use_guards(OAuthGuard, create_scope_guard(["read"]))
async def search_flights(self, input: SearchFlightsInput, context: ExecutionContext) -> dict:
    ...
```

Same pattern: `use_middleware`, `use_interceptors`, `use_pipes`, `use_filters`.

## Protocols

Implement these as classes (often returned from a factory):

- **Guard** — `async def can_activate(self, context: ExecutionContext) -> bool`
- **Middleware** — `async def use(self, context, next_fn)`
- **Interceptor** — `async def intercept(self, context, next_fn)`
- **Pipe** — `async def transform(self, value, metadata: PipeMetadata)`
- **ExceptionFilter** — `async def catch(self, error, context)`

Scaffold with `nitrostack-py generate guard|pipe|interceptor|filter <Name>`.

## Built-ins

- `ApiKeyGuard` — `x-api-key` in metadata/headers; `ApiKeyService` or `API_KEY` env.
- `JwtGuard` — `Authorization: Bearer`; fills `context.auth`.
- `OAuthGuard` — introspects the access token; see the auth-security skill.

Read tokens from `context.metadata` (`authorization`, `headers`, `_oauth`). Do not assume Express/Nest request objects.

## Do not

- Use TypeScript `UseGuards()` / Nest middleware.
- Fail closed on missing OAuth when `OAUTH_REQUIRED` is unset — `OAuthGuard` allows no-token when oauth is not required (Studio mock flights).
