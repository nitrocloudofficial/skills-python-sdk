---
name: nitrostack-python-middleware-pipeline
description: Guards, middleware, interceptors, pipes, and exception filters on NitroStack Python tools.
---

## When to Use

Authorizing or transforming a tool/resource/prompt call in the **Python** SDK (`nitrostack.core.pipeline`).

## Stages

Each stage is a small class with one async method. Attach it with a decorator below `@tool`.

| Stage | Method | Attach with | Runs |
|---|---|---|---|
| Guard | `can_activate(context) -> bool` | `@use_guards(...)` | first; `False` rejects the call ("Access denied by guard") |
| Pipe | `transform(value, metadata: PipeMetadata)` | `@use_pipes(...)` | on the tool input, after guards |
| Middleware | `use(context, next_fn)` | `@use_middleware(...)` | around interceptors and the tool |
| Interceptor | `intercept(context, next_fn)` | `@use_interceptors(...)` | around the tool; can change its result |
| Exception filter | `catch(error, context)` | `@use_filters(...)` | on errors; its return value becomes the result |

`PipeMetadata` (`param_name`, `param_type`) is imported from `nitrostack.core.pipeline`.

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

A guard factory (a function returning a guard class) is fine when the guard needs parameters; see `create_scope_guard` in the oauth template.

Scaffold with `nitrostack-py generate guard|pipe|interceptor|filter <Name>` (writes `guards/`, `pipes/`, `interceptors/`, `filters/`).

## Built-in guards

- `ApiKeyGuard`: checks the `x-api-key` header against `ApiKeyModule` keys. Register `ApiKeyModule.for_root()` when you use it: without the module the guard falls back to the `API_KEY` variable, and with neither set it **lets every call through**.
- `JwtGuard`: `Authorization: Bearer <jwt>`, configured by `JWTModule`; fills `context.auth`.
- `OAuthGuard`: introspects or verifies the OAuth access token; see the auth-security skill.
- `require_scopes("admin")`: stack under an auth guard; rejects unless `context.auth` has every listed scope.

Read tokens and request data from `context.metadata` (`authorization`, `headers`, `_oauth`). There are no Express/Nest request objects.

## Do not

- Use TypeScript `UseGuards()` / Nest middleware.
- Fail closed on missing OAuth when `OAUTH_REQUIRED` is unset. `OAuthGuard` allows no-token calls when OAuth is not required (local Studio/Inspector).
- Use `ApiKeyGuard` without `ApiKeyModule` or `API_KEY`: it then protects nothing.
