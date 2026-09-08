---
name: nitrostack-python-middleware-pipeline
description: Best practices for implementing and applying Guards, Interceptors, Middleware, Pipes, and Exception Filters in NitroStack Python MCP servers.
---

## When to Use
Use this skill when implementing request authorization, input transformation, execution timing, error handling, or logging on NitroStack Python tools, resources, and prompts.

---

## Pipeline Execution Order

When an MCP client invokes a tool handler, NitroStack executes the pipeline in the following sequence:
1. **Guards** (`@use_guards`): Verify authentication/authorization (`can_activate`).
2. **Pipes** (`@use_pipes`): Transform/validate raw inputs (`transform`).
3. **Middleware** (`@use_middleware`): Wrap execution before/after handler (`use`).
4. **Interceptors** (`@use_interceptors`): Intercept or transform results (`intercept`).
5. **Handler**: The actual `@tool` async method execution.
6. **Exception Filters** (`@use_filters`): Catch and map any uncaught exceptions into user-friendly responses (`catch`).

---

## 1. Guards (`Guard` and `@use_guards`)

Guards control access before reaching pipes or handlers.

### Protocol:
```python
from nitrostack import ExecutionContext

class Guard:
    async def can_activate(self, context: ExecutionContext) -> bool:
        ...
```

### Example:
```python
from nitrostack import injectable, ExecutionContext

@injectable()
class RolesGuard:
    async def can_activate(self, context: ExecutionContext) -> bool:
        user_roles = context.auth.claims.get("roles", []) if context.auth else []
        return "admin" in user_roles
```

### Usage on Tools:
```python
from nitrostack import injectable, tool, use_guards, ExecutionContext
from pydantic import BaseModel

class PurgeLogsInput(BaseModel):
    before_date: str

@injectable()
class LogTools:
    @tool(name="purge_logs", description="Purge system logs", input_schema=PurgeLogsInput)
    @use_guards(RolesGuard)
    async def purge_logs(self, input: PurgeLogsInput, context: ExecutionContext) -> dict:
        return {"purged": True}
```

---

## 2. Interceptors (`Interceptor` and `@use_interceptors`)

Interceptors wrap handler execution to measure duration, modify results, or log operations.

### Protocol:
```python
from typing import Callable, Any
from nitrostack import ExecutionContext

class Interceptor:
    async def intercept(self, context: ExecutionContext, next_fn: Callable[[], Any]) -> Any:
        ...
```

### Example:
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
        if isinstance(result, dict):
            result["_meta"] = {"duration_ms": duration_ms}
        return result
```

---

## 3. Exception Filters (`ExceptionFilter` and `@use_filters`)

Exception filters catch uncaught errors thrown anywhere in the execution chain and format clean error responses.

### Protocol:
```python
from nitrostack import ExecutionContext

class ExceptionFilter:
    async def catch(self, error: Exception, context: ExecutionContext) -> Any:
        ...
```

### Example:
```python
from nitrostack import injectable, ExecutionContext

@injectable()
class CustomExceptionFilter:
    async def catch(self, error: Exception, context: ExecutionContext) -> dict:
        context.logger.error(f"Captured exception: {error}")
        return {
            "error": True,
            "message": str(error),
            "tool": context.tool_name,
        }
```

---

## 4. Middleware (`Middleware` and `@use_middleware`)

Middleware executes before and after the handler by calling `await next_fn()`.

### Protocol:
```python
from typing import Callable, Any
from nitrostack import ExecutionContext

class Middleware:
    async def use(self, context: ExecutionContext, next_fn: Callable[[], Any]) -> Any:
        ...
```

### Example:
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

## 5. Pipes (`Pipe` and `@use_pipes`)

Pipes transform or validate tool input arguments before they reach the handler.

### Protocol:
```python
from typing import Any
from nitrostack.core.pipeline import PipeMetadata

class Pipe:
    async def transform(self, value: Any, metadata: PipeMetadata) -> Any:
        ...
```

### Example:
```python
from nitrostack import injectable
from nitrostack.core.pipeline import PipeMetadata

@injectable()
class TrimStringPipe:
    async def transform(self, value: Any, metadata: PipeMetadata) -> Any:
        if isinstance(value, str):
            return value.strip()
        if hasattr(value, "__dict__"):
            for k, v in value.__dict__.items():
                if isinstance(v, str):
                    setattr(value, k, v.strip())
        return value
```

---

## Stacking Multiple Pipeline Decorators

```python
from nitrostack import (
    injectable,
    tool,
    use_guards,
    use_pipes,
    use_middleware,
    use_interceptors,
    use_filters,
    ExecutionContext,
)

@injectable()
class SecureOperationTools:
    @tool(name="execute_task", description="Executes sensitive task", input_schema=TaskInput)
    @use_guards(RolesGuard)
    @use_pipes(TrimStringPipe)
    @use_middleware(LoggingMiddleware)
    @use_interceptors(TimingInterceptor)
    @use_filters(CustomExceptionFilter)
    async def execute_task(self, input: TaskInput, context: ExecutionContext) -> dict:
        return {"status": "completed"}
```

---

## Built-in Guards
- **`ApiKeyGuard`**: Validates `x-api-key` metadata/headers with `ApiKeyService`.
- **`JwtGuard`**: Validates Bearer JWTs and populates `context.auth`.
- **`OAuthGuard`**: Introspects OAuth 2.1 access tokens and populates `context.auth`.

---

## CLI Generators
Generate boilerplate classes matching the Python SDK signatures:
```bash
nitrostack-py generate guard AdminGuard
nitrostack-py generate pipe SanitizeInput
nitrostack-py generate interceptor Metrics
nitrostack-py generate filter GlobalException
```

---

## Do Not
- Do not use TypeScript NestJS decorator names (`@UseGuards()` in camelCase). Use snake_case `use_guards`, `use_middleware`, etc.
- Do not forget `await next_fn()` in middleware and interceptors.
- Do not access raw HTTP `Request` objects; use `context.metadata` and `context.auth`.
