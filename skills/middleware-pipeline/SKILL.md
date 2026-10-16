---
name: nitrostack-python-middleware-pipeline
description: Guards, middleware, interceptors, pipes, and exception filters on NitroStack Python tools.
---

## When to Use

Authorizing or transforming a tool/resource/prompt call in the **Python** SDK (`nitrostack.core.pipeline`).

## Pipeline execution order

When a client invokes a tool, NitroStack runs:

1. **Guards** (`@use_guards`): `can_activate` — `False` rejects with "Access denied by guard".
2. **Pipes** (`@use_pipes`): `transform` on tool input.
3. **Middleware** (`@use_middleware`): `use` wraps execution.
4. **Interceptors** (`@use_interceptors`): `intercept` around the handler.
5. **Handler**: the `@tool` method.
6. **Exception filters** (`@use_filters`): `catch` maps uncaught errors to a return value.

| Stage | Method | Attach with |
|---|---|---|
| Guard | `can_activate(context) -> bool` | `@use_guards(...)` |
| Pipe | `transform(value, metadata: PipeMetadata)` | `@use_pipes(...)` |
| Middleware | `use(context, next_fn)` | `@use_middleware(...)` |
| Interceptor | `intercept(context, next_fn)` | `@use_interceptors(...)` |
| Exception filter | `catch(error, context)` | `@use_filters(...)` |

`PipeMetadata` (`param_name`, `param_type`) is imported from `nitrostack.core.pipeline`.

---

## 1. Guards

```python
from nitrostack import injectable, tool, use_guards, ExecutionContext
from pydantic import BaseModel

class PurgeLogsInput(BaseModel):
    before_date: str

@injectable()
class RolesGuard:
    async def can_activate(self, context: ExecutionContext) -> bool:
        user_roles = context.auth.claims.get("roles", []) if context.auth else []
        return "admin" in user_roles

@injectable()
class LogTools:
    @tool(name="purge_logs", description="Purge system logs", input_schema=PurgeLogsInput)
    @use_guards(RolesGuard)
    async def purge_logs(self, input: PurgeLogsInput, context: ExecutionContext) -> dict:
        return {"purged": True}
```

A guard factory (a function returning a guard class) is fine when the guard needs parameters; see `create_scope_guard` in the oauth template.

---

## 2. Interceptors

```python
import time
from nitrostack import injectable, ExecutionContext

@injectable()
class TimingInterceptor:
    async def intercept(self, context: ExecutionContext, next_fn):
        start = time.time()
        result = await next_fn()
        duration_ms = (time.time() - start) * 1000
        context.logger.info(f"Tool {context.tool_name} executed in {duration_ms:.2f}ms")
        return result
```

---

## 3. Exception filters

```python
from nitrostack import injectable, ExecutionContext

@injectable()
class CustomExceptionFilter:
    async def catch(self, error: Exception, context: ExecutionContext) -> dict:
        context.logger.error(f"Captured exception: {error}")
        return {"error": True, "message": str(error), "tool": context.tool_name}
```

---

## 4. Middleware

```python
from nitrostack import injectable, ExecutionContext

@injectable()
class LoggingMiddleware:
    async def use(self, context: ExecutionContext, next_fn):
        context.logger.info(f"--> Entering tool: {context.tool_name}")
        try:
            result = await next_fn()
            context.logger.info(f"<-- Exiting tool: {context.tool_name}")
            return result
        except Exception as exc:
            context.logger.error(f"Error in tool {context.tool_name}: {exc}")
            raise exc
```

---

## 5. Pipes

```python
from typing import Any
from nitrostack import injectable
from nitrostack.core.pipeline import PipeMetadata

@injectable()
class TrimStringPipe:
    async def transform(self, value: Any, metadata: PipeMetadata) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value
```

---

## Stacking decorators

Decorator order on the method (bottom = runs first): `@tool`, then `@use_guards`, `@use_pipes`, `@use_middleware`, `@use_interceptors`, `@use_filters`.

```python
from pydantic import BaseModel
from nitrostack import injectable, tool, use_guards, use_interceptors, use_filters, ExecutionContext

class LookupInput(BaseModel):
    city: str

class OfficeHoursGuard:
    async def can_activate(self, context: ExecutionContext) -> bool:
        return context.metadata.get("office_open", True)

class TimingInterceptor:
    async def intercept(self, context: ExecutionContext, next_fn):
        result = await next_fn()
        context.logger.info(f"{context.tool_name} finished")
        return result

class FriendlyErrors:
    async def catch(self, error: Exception, context: ExecutionContext):
        return {"error": str(error)}

@injectable()
class WeatherTools:
    @tool(name="get_forecast", description="Forecast for a city", input_schema=LookupInput)
    @use_guards(OfficeHoursGuard)
    @use_interceptors(TimingInterceptor)
    @use_filters(FriendlyErrors)
    async def get_forecast(self, input: LookupInput, context: ExecutionContext) -> dict:
        return {"city": input.city, "forecast": "sunny"}
```

Scaffold with `nitrostack-py generate guard|pipe|interceptor|filter <Name>` (writes `guards/`, `pipes/`, `interceptors/`, `filters/`).

## Built-in guards

- `ApiKeyGuard`: checks the `x-api-key` header against `ApiKeyModule` keys. Register `ApiKeyModule.for_root()` when you use it: without the module the guard falls back to the `API_KEY` variable, and with neither set it **lets every call through**.
- `JwtGuard`: `Authorization: Bearer <jwt>`, configured by `JWTModule`; fills `context.auth`.
- `OAuthGuard`: introspects or verifies the OAuth access token; see the auth-security skill.
- `require_scopes("admin")`: stack under an auth guard; rejects unless `context.auth` has every listed scope.

Read tokens and request data from `context.metadata` (`authorization`, `headers`, `_oauth`). There are no Express/Nest request objects.

## Do not

- Use TypeScript `UseGuards()` / Nest middleware naming; use snake_case `use_guards`, `use_middleware`, etc.
- Forget `await next_fn()` in middleware and interceptors.
- Fail closed on missing OAuth when `OAUTH_REQUIRED` is unset. `OAuthGuard` allows no-token calls when OAuth is not required (local Studio/Inspector).
- Use `ApiKeyGuard` without `ApiKeyModule` or `API_KEY`: it then protects nothing.
