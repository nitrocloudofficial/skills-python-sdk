---
name: nitrostack-python-ui-widgets
description: Python NitroStack MCP Apps widgets — @widget, widgets/out HTML, WidgetOptions, and preview.
---

## When to Use

Attaching UI to a Python tool result (Calculator, Pizzaz, flight-booking). Not `@nitrostack/ui` npm widgets.

## Associate a widget with a tool

Decorate any `@tool` method with `@widget("route-name")` or `@widget(WidgetOptions(...))`.

```python
from pydantic import BaseModel
from nitrostack import injectable, tool, widget, WidgetOptions, WidgetCsp, ExecutionContext

class CalculateInput(BaseModel):
    a: float
    b: float

class MapInput(BaseModel):
    city: str

@injectable()
class WidgetTools:
    @tool(name="calculate", description="Add two numbers", input_schema=CalculateInput)
    @widget("calculator-result")
    async def calculate(self, input: CalculateInput, context: ExecutionContext) -> dict:
        return {"result": input.a + input.b, "expression": f"{input.a} + {input.b}"}

    @tool(name="show_pizza_map", description="Pizza shops on a map", input_schema=MapInput)
    @widget(WidgetOptions(
        route="pizza-map",
        prefers_border=True,
        csp=WidgetCsp(
            resource_domains=["https://api.mapbox.com"],
            connect_domains=["https://api.mapbox.com"],
        ),
    ))
    async def show_pizza_map(self, input: MapInput, context: ExecutionContext) -> dict:
        return {"city": input.city, "shops": []}
```

Return JSON/`dict` from the tool; the widget HTML reads `structuredContent` / injected tool data. Do not return a React tree from Python.

The SDK registers `ui://widget/<route>.html` as an MCP resource and adds widget `_meta` to `tools/list` and `tools/call` results.

## Application modes (`NITROSTACK_APP_MODE`)

| Mode | Tool `_meta` | Resource MIME type |
|---|---|---|
| `universal` (default) | Both OpenAI (`openai/outputTemplate`) and MCP Apps (`_meta.ui`) | `text/html;profile=mcp-app` |
| `mcp-app` | MCP Apps UI metadata (`resourceUri`, visibility, CSP) | `text/html;profile=mcp-app` |
| `openai` | OpenAI template metadata (`ui/template`, `outputTemplate`) | `text/html` |

`init` sets `universal` by default so one server works with OpenAI and MCP Apps hosts.

## Files

- `widgets/out/<route>.html`: the page the MCP host loads. `nitrostack-py init` creates a missing one for every route in `@widget("...")` and `WidgetOptions(route="...")`. The SDK also looks in `src/widgets/out` and `dist/widgets/out`.
- `widgets/preview.html`: static helper. Live preview: `http://localhost:3000/widgets/preview`.
- Optional `src/widgets/` Next.js app: when present, `init` runs `npm install` there and `nitrostack-py dev` starts it on `WIDGETS_DEV_PORT` (default 3001). Bundled templates ship plain HTML in `widgets/out`. MCP server port is `PORT` (default 3000).
- Widget pages are self-contained: plain CSS (inline styles, a `<style>` block, or CSS modules). Do not depend on Tailwind.

## Data flow

1. The `@tool` method returns a `dict` or Pydantic model.
2. NitroStack embeds serialized data as `structuredContent` in the MCP response metadata.
3. The widget HTML loads in the host webview and reads injected data via the MCP Apps bridge (`window.addEventListener('message', ...)`).

## Development and Inspector

```bash
nitrostack-py dev --port 3000 --widget 3001
```

For MCP Inspector over HTTP (stateless):

```bash
MCP_TRANSPORT_TYPE=http MCP_STATELESS=true NITROSTACK_APP_MODE=universal python main.py
```

- Connect to `http://localhost:3000/mcp` (Streamable HTTP, no trailing slash).
- Turn **Authentication off** in Inspector unless testing OAuth (otherwise it POSTs `/register` and fails with `Cannot POST /register`).
- Use the **Apps** tab for live widget rendering.

## Do not

- Scaffold a TypeScript widget package as the source of truth for Python tools.
- Use complex nested route paths; use kebab-case names (`calculator-result`, `flight-results`).
- Set `_meta.ui.resourceUri` to anything other than a `ui://widget/...` URI.
- Run TypeScript `@nitrostack/widgets` hooks directly in Python runtime code.
