---
name: nitrostack-python-runtime-features
description: Caching, rate limits, long-running MCP tasks with progress, events, and health checks in NitroStack Python.
---

## When to Use

A tool is slow or expensive (cache it, rate-limit it, or run it as a task), or one part of the app must react to another (events), or the server needs a health signal.

## Caching and rate limits

```python
from pydantic import BaseModel
from nitrostack import cache, injectable, rate_limit, tool, ExecutionContext

class NoInput(BaseModel):
    pass

@injectable()
class WeatherService:
    @cache(ttl=60)  # seconds; keyed on the arguments
    async def lookup(self, city: str) -> dict:
        return {"city": city, "temp": 21}

@injectable(deps=[WeatherService])
class WeatherTools:
    def __init__(self, service: WeatherService):
        self.service = service

    @tool(name="ping", description="Ping", input_schema=NoInput)
    @rate_limit(max=10, window=60)  # 10 calls per 60 s, across all callers
    async def ping(self, input: NoInput, context: ExecutionContext) -> str:
        return "pong"
```

Put `@cache` on a **service** method with plain, hashable arguments (strings, numbers, tuples). On a tool method it fails with `unhashable type`, because the tool's input is a Pydantic object. Over the limit, `@rate_limit` returns "Rate limit exceeded".

## Long-running tasks

Set `task_support="optional"` (or `"required"`) and the client can run the tool as an MCP task: it polls `tasks/get`, can cancel, and gets live `notifications/progress` when it sends a `progressToken`. `context.task` is `None` on a normal call, so guard every use.

```python
import asyncio
from pydantic import BaseModel
from nitrostack import injectable, tool, ExecutionContext

class ReportInput(BaseModel):
    steps: int = 5

@injectable()
class ReportTools:
    @tool(name="build_report", description="Build a report", input_schema=ReportInput, task_support="optional")
    async def build_report(self, input: ReportInput, context: ExecutionContext) -> dict:
        for step in range(1, input.steps + 1):
            if context.task:
                context.task.update_progress(f"Step {step}/{input.steps}")
                context.task.throw_if_cancelled()
            await asyncio.sleep(1)
        return {"steps": input.steps}
```

## Events

```python
from typing import List
from nitrostack import EventEmitter, injectable, on_event

@injectable()
class OrderService:
    async def place(self, order_id: str) -> None:
        await EventEmitter.get_instance().emit("order.placed", {"id": order_id})

@injectable()
class AuditLog:
    def __init__(self):
        self.entries: List[str] = []

    @on_event("order.placed")
    def record(self, payload: dict) -> None:
        self.entries.append(payload["id"])
```

`@on_event` methods are bound on any provider or controller of a module at startup. The emitter is in-process; it is not a message queue.

## Health checks

```python
from nitrostack import health_check, injectable

@injectable()
class DatabaseHealth:
    @health_check("database")
    def check(self) -> bool:
        return True
```

When any health check exists, the server exposes the `health://status` resource (`{"database": "healthy"}`). Keep health checks synchronous and fast. Over HTTP, `GET /mcp/health` reports the transport (sessions, uptime).

## Do not

- Cache tool methods, or results that depend on the caller's identity.
- Call `context.task.update_progress` without checking `context.task`.
- Use `async def` health checks.
