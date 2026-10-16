---
name: nitrostack-python-ui-widgets
description: Best practices for linking Python MCP tools to UI widgets, WidgetOptions, CSP, application modes, and preview.
---

## When to Use
Use this skill when attaching UI widgets to Python MCP tool outputs (e.g. interactive cards, map views, flight cards, or forms) and configuring widget routes, CSP, and preview rendering.

---

## 1. Associating a Widget with a Tool (`@widget`)

Decorate any `@tool` method with `@widget("route-name")` or with `@widget(WidgetOptions(...))` to bind frontend HTML/React components to tool results.

### Simple Route Binding:
```python
from nitrostack import injectable, tool, widget, ExecutionContext
from pydantic import BaseModel

class ProductInput(BaseModel):
    product_id: str

@injectable()
class StoreTools:
    @tool(name="get_product", description="Fetch product card", input_schema=ProductInput)
    @widget("product-card")  # Maps to widgets/out/product-card.html
    async def get_product(self, input: ProductInput, context: ExecutionContext) -> dict:
        return {
            "name": "Super Nitro Coffee",
            "price": 4.99,
            "stock": 42,
        }
```

### Advanced WidgetOptions with CSP & Border:
```python
from nitrostack import injectable, tool, widget, WidgetOptions, WidgetCsp, ExecutionContext
from pydantic import BaseModel

class LocationInput(BaseModel):
    city: str

@injectable()
class MapTools:
    @tool(name="show_store_map", description="Show interactive map of stores", input_schema=LocationInput)
    @widget(
        WidgetOptions(
            route="store-map",
            prefers_border=True,
            csp=WidgetCsp(
                resource_domains=["https://api.mapbox.com", "https://events.mapbox.com"],
                connect_domains=["https://api.mapbox.com"],
            ),
        )
    )
    async def show_map(self, input: LocationInput, context: ExecutionContext) -> dict:
        return {"city": input.city, "stores": [{"name": "Downtown", "lat": 37.77, "lng": -122.41}]}
```

---

## 2. Application Modes (`NITROSTACK_APP_MODE`)

NitroStack supports mode-gated metadata to serve OpenAI and MCP Apps clients simultaneously via the `NITROSTACK_APP_MODE` environment variable (default: `universal`):

| Mode | Tool `_meta` | Resource MIME Type |
|---|---|---|
| `universal` (default) | Populates both OpenAI (`openai/outputTemplate`) and MCP Apps (`_meta.ui`) | `text/html;profile=mcp-app` |
| `mcp-app` | Standard MCP Apps UI metadata (`resourceUri`, `visibility`, CSP) | `text/html;profile=mcp-app` |
| `openai` | OpenAI template metadata (`ui/template`, `outputTemplate`) | `text/html` |

---

## 3. Widget Files & Directory Layout

- **`widgets/out/{route}.html`**: The production HTML bundle rendered inside the MCP host's webview. NitroStack automatically exposes this file as an MCP resource with URI `ui://widget/{route}.html`.
- **`widgets/preview.html`**: Static preview page for inspecting widget templates during development.
- **`src/widgets/`** (optional): Next.js or React frontend source app when using a multi-package setup.

---

## 4. Widget Data Flow Protocol

1. **Python Tool Execution**: The `@tool` method executes and returns standard Python `dict` or Pydantic `BaseModel` data.
2. **Host Delivery**: NitroStack embeds the serialized data as `structuredContent` in the MCP JSON-RPC response metadata.
3. **Webview Rendering**: The widget HTML bundle loads inside the client iframe and reads the injected tool data via the standard MCP Apps bridge (`window.addEventListener('message', ...)`).

> [!IMPORTANT]
> Always return clean domain data (`dict` or Pydantic models) from your Python `@tool` methods. Do not return raw React or HTML trees from Python handlers.

---

## 5. Development & Testing Workflow

### Running Dev Server with Hot-Reload:
```bash
nitrostack-py dev --port 3000 --widget 3001
```

### Testing in MCP Inspector:
For MCP Inspector over HTTP, run in stateless mode:
```bash
MCP_TRANSPORT_TYPE=http MCP_STATELESS=true NITROSTACK_APP_MODE=universal python main.py
```
- Connect MCP Inspector to `http://localhost:3000/mcp` (Streamable HTTP, no trailing slash).
- Turn **Authentication off** in Inspector (unless actively testing OAuth endpoints).
- Navigate to the **Apps** tab to view live interactive widget rendering.
- Live widget preview is also accessible directly at: `http://localhost:3000/widgets/preview`.

---

## Do Not
- Do not set `_meta.ui.resourceUri` to anything other than a `ui://widget/...` URI.
- Do not use complex nested route paths; use clean kebab-case names (e.g. `product-card`, `flight-results`).
- Do not attempt to run TypeScript `@nitrostack/widgets` hooks directly in Python runtime code.
