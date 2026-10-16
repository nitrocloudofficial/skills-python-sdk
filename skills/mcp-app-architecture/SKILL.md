---
name: nitrostack-python-mcp-app-architecture
description: Bootstrapping a NitroStack Python MCP server — AppModule, modules, DI, and McpApplicationFactory.
---

## When to Use

Use this skill when creating or changing a NitroStack **Python** MCP server: root module, feature modules, providers, or process startup. Do not use TypeScript `@McpApp`, `@Module`, or Zod.

## Bootstrapping

Generated apps start from `main.py` with `McpApplicationFactory.create` and the root `AppModule`. There is no required `@mcp_app` class in the starter templates.

```python
import asyncio
from nitrostack import McpApplicationFactory
from app_module import AppModule

async def main():
    app = await McpApplicationFactory.create(AppModule)
    await app.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### With `ServerConfig` and transport in code (`@mcp_app`):

```python
import asyncio
from nitrostack import mcp_app, McpApplicationFactory, ServerConfig
from app_module import AppModule

@mcp_app(
    module=AppModule,
    server=ServerConfig(
        name="my-mcp-server",
        version="1.0.0",
        transport_type="stdio",  # "stdio", "http", or "dual"
        max_sessions=100,
        session_timeout_ms=1800000,
    ),
)
class App:
    pass

async def main():
    app = await McpApplicationFactory.create(App)
    await app.start()

if __name__ == "__main__":
    asyncio.run(main())
```

Transport flags and env overrides are documented in the transports-cli skill.

The server name clients show comes from `SERVER_NAME` (set to the project folder by `init`) whenever the configured name is generic (`app`, `mcp-server`). Rename the project by changing `SERVER_NAME` in `.env`, not the root module's `name`.

## Root AppModule

```python
from nitrostack import module, ConfigModule
from modules.calculator.calculator_module import CalculatorModule
from health.system_health import SystemHealthCheck

@module(
    name="app",
    imports=[
        ConfigModule.for_root(env_file_path=".env", defaults={"PORT": "3000"}),
        CalculatorModule,
    ],
    providers=[SystemHealthCheck],
)
class AppModule:
    pass
```

`@module(...)` takes `name`, `controllers`, `providers`, `imports`, `exports`. Feature tools go on **controllers**. Injectable services go on **providers**. `imports` pull in other modules (and `ConfigModule`, `ApiKeyModule`, `JWTModule`, `OAuthModule`).

## Feature modules

One directory per feature under `modules/`.

- **controllers**: classes with `@tool`, `@resource`, or `@prompt`.
- **providers**: services managed by the DI container.
- **imports**: other modules whose exported providers are needed here.
- **exports**: providers made available to modules that import this one.

```
modules/fixtures/
  fixtures_module.py    # @module(...)
  fixtures_service.py   # DB queries, business logic
  fixtures_tools.py     # @tool methods that call the service
```

```python
from nitrostack import module
from modules.calculator.calculator_tools import CalculatorTools
from modules.calculator.calculator_service import CalculatorService

@module(
    name="calculator",
    controllers=[CalculatorTools],
    providers=[CalculatorService],
    exports=[CalculatorService],
)
class CalculatorModule:
    pass
```

Scaffold with `nitrostack-py generate module <name>` and `nitrostack-py generate service <Name>` (see transports-cli skill for other generators).

## Dependency injection

Mark classes `@injectable()` or `@injectable(deps=[SomeService])`. Constructor args must match `deps`. The container instantiates controllers and providers as singletons; do not call `SomeService()` by hand inside a tool class.

```python
from nitrostack import injectable

@injectable()
class PizzazService:
    def list_shops(self) -> list:
        return []

@injectable(deps=[PizzazService])
class PizzazTools:
    def __init__(self, service: PizzazService):
        self.service = service
```

Settings come from `ConfigService` (config-environment skill).

## Health checks and events

Register a provider with `@health_check("system")` on a method that returns a bool (see `health/system_health.py`). Caching, rate limits, long-running tasks, and the event bus are in the runtime-features skill.

## Do not

- Import `@nitrostack/core` or write TypeScript decorators.
- Put `@tool` methods on a module class that is only a `@module` config holder.
- Skip `ConfigModule.for_root` if the app reads `.env`.
- Write database queries inside tool methods. Put them in a service.
- Instantiate services manually with `SomeService()`; use constructor DI via `@injectable(deps=[...])`.
