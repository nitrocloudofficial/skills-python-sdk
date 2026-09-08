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

Optional: `@mcp_app(module=AppModule, server=ServerConfig(name="...", version="1.0.0"))` exists on a class, but factory-from-module is the template path.

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

`@module(...)` takes `name`, `controllers`, `providers`, `imports`, `exports`. Feature tools go on **controllers**. Injectable services go on **providers**. `imports` pull in other modules (and `ConfigModule` / `OAuthModule`).

## Feature modules

Put `@tool` / `@resource` / `@prompt` classes in `controllers`. Put services the controllers construct in `providers` and `exports` if other modules need them.

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

## Dependency injection

Mark classes `@injectable()` or `@injectable(deps=[SomeService])`. Constructor args must match `deps`. The container instantiates controllers and providers; do not `SomeService()` by hand inside a tool class.

```python
from nitrostack import injectable

@injectable(deps=[PizzazService])
class PizzazTools:
    def __init__(self, service: PizzazService):
        self.service = service
```

## Health checks

Register a provider with `@health_check("system")` on a method that returns a bool (see `health/system_health.py`).

## Do not

- Import `@nitrostack/core` or write TypeScript decorators.
- Put `@tool` methods on a module class that is only a `@module` config holder.
- Skip `ConfigModule.for_root` if the app reads `.env`.
