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

Optional: `@mcp_app(module=AppModule, server=ServerConfig(name="...", version="1.0.0"))` on a class sets the server name, transport and session limits in code (transports-cli skill). Factory-from-module is the template path.

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

One directory per feature under `modules/`. Put `@tool` / `@resource` / `@prompt` classes in `controllers`. Put services in `providers`, and in `exports` if other modules need them.

```
modules/fixtures/
  fixtures_module.py    # @module(...)
  fixtures_service.py   # DB queries, business logic
  fixtures_tools.py     # @tool methods that call the service
```

```python
from nitrostack import module
from modules.calculator.calculator_tools import CalculatorTools

@module(
    name="calculator",
    controllers=[CalculatorTools],
    providers=[],
    exports=[],
)
class CalculatorModule:
    pass
```

Scaffold with `nitrostack-py generate module <name>` and `nitrostack-py generate service <Name>`.

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

Register a provider with `@health_check("system")` on a method that returns a bool (see `health/system_health.py`). Events, caching, rate limits and long-running tasks are in the runtime-features skill.

## Do not

- Import `@nitrostack/core` or write TypeScript decorators.
- Put `@tool` methods on a module class that is only a `@module` config holder.
- Skip `ConfigModule.for_root` if the app reads `.env`.
- Write database queries inside tool methods. Put them in a service.
