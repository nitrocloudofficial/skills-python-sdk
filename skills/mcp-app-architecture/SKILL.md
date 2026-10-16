---
name: nitrostack-python-mcp-app-architecture
description: Bootstrapping a NitroStack Python MCP server — AppModule, modules, DI, events, lifecycles, and McpApplicationFactory.
---

## When to Use
Use this skill when creating, structuring, or refactoring a NitroStack **Python** MCP server: configuring the root module, organizing feature modules, managing dependencies via DI, emitting/handling events, registering health checks, or configuring server transports.

---

## 1. Bootstrapping an Application

NitroStack Python applications can be started using `McpApplicationFactory.create(...)` with the root module or `@mcp_app` class.

### Standard Entrypoint (`main.py`):
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

### With ServerConfig & Transport Options (`@mcp_app`):
```python
import asyncio
from nitrostack import mcp_app, McpApplicationFactory, ServerConfig
from app_module import AppModule

@mcp_app(
    module=AppModule,
    server=ServerConfig(
        name="my-mcp-server",
        version="1.0.0",
        transport_type="stdio",  # Options: "stdio", "http", or "dual" (runs stdio + http together)
        max_sessions=100,        # Max concurrent HTTP sessions
        session_timeout_ms=1800000, # 30 min idle timeout
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

---

## 2. Root AppModule & Configuration

The root module aggregates imported feature modules, global services, and configuration.

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

---

## 3. Feature Modules & Separation of Concerns

Modules organize tools and services into isolated domain boundaries.
- **`controllers`**: Classes containing `@tool`, `@resource`, or `@prompt` definitions.
- **`providers`**: Services, repositories, or helpers managed by the DI container.
- **`imports`**: Other modules whose exported providers are needed here.
- **`exports`**: Providers from this module made available to other modules that import it.

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

---

## 4. Dependency Injection (DI)

Mark classes with `@injectable()` or `@injectable(deps=[...])`. Constructor parameters must match the declared dependencies in `deps`.

```python
from nitrostack import injectable

@injectable()
class DatabaseService:
    def query(self, sql: str) -> list:
        return []

@injectable(deps=[DatabaseService])
class UserService:
    def __init__(self, db: DatabaseService):
        self.db = db

@injectable(deps=[UserService])
class UserTools:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
```

> [!NOTE]
> The DI container automatically resolves and instantiates singletons for all controllers and providers registered in active modules. Do not instantiate `@injectable` services manually inside tool methods.

---

## 5. Event System (`EventEmitter` and `@on_event`)

NitroStack includes an asynchronous internal event system to decouple services and modules.

### Emitting Events:
```python
from nitrostack import injectable, EventEmitter

@injectable()
class OrderService:
    async def place_order(self, order_id: str, amount: float):
        # Process order logic...
        
        # Emit event to all registered listeners
        await EventEmitter.get_instance().emit(
            "order.placed",
            {"order_id": order_id, "amount": amount}
        )
```

### Listening to Events with `@on_event`:
Decorate any method inside an `@injectable` provider or controller with `@on_event("event_name")`:

```python
from nitrostack import injectable, on_event

@injectable()
class NotificationService:
    @on_event("order.placed")
    async def on_order_placed(self, payload: dict):
        order_id = payload.get("order_id")
        print(f"Sending confirmation email for order {order_id}")
```

---

## 6. Health Checks (`@health_check`)

Register health checks on providers or controllers to expose system status on the `/mcp/health` endpoint:

```python
from nitrostack import injectable, health_check

@injectable()
class SystemHealthCheck:
    @health_check("database")
    async def check_database(self) -> bool:
        # Return True for healthy, False for unhealthy
        return True
```

---

## 7. CLI Lifecycle (`nitrostack-py`)

- `nitrostack-py init [name] [--template python-starter|python-pizzaz|python-oauth]`
- `nitrostack-py dev [--port 3000] [--widget 3001]` (hot reload)
- `nitrostack-py start` (production runner)
- `nitrostack-py generate tool|module|guard|pipe|interceptor|filter|service <Name>`
- `nitrostack-py pack` (builds deployable wheel in `dist/`)
- `nitrostack-py validate` (lints imports, modules, and dependencies)
- `nitrostack-py register --name my-server --file app.py` (registers with Claude Desktop)

---

## Do Not
- Do not import `@nitrostack/core` or use TypeScript `@Module` syntax.
- Do not define `@tool` methods directly on module configuration classes. Put them on controller classes.
- Do not instantiate services manually with `SomeService()`; use constructor DI via `@injectable(deps=[...])`.
