---
name: nitrostack-python-ui-widgets
description: Python NitroStack MCP Apps widgets — @widget, widgets/out HTML, WidgetOptions, and preview.
---

## When to Use

Attaching UI to a Python tool result (Calculator, Pizzaz, flight-booking). Not `@nitrostack/ui` npm widgets.

## Associate a widget with a tool

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

    # Object form, for CSP and border options
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

The SDK registers `ui://widget/<route>.html` as an MCP resource and adds the widget `_meta` to `tools/list` and `tools/call` results.

## Files

- `widgets/out/<route>.html`: the page the MCP host loads. `nitrostack-py init` creates a missing one for every route it finds in `@widget("...")` and `WidgetOptions(route="...")`. The SDK also looks in `src/widgets/out` and `dist/widgets/out`.
- `widgets/preview.html`: a static helper, not the live result. Live preview: `http://localhost:3000/widgets/preview`.
- Optional `src/widgets/` Next.js app: when present, `init` runs `npm install` there and `nitrostack-py dev` starts it on `WIDGETS_DEV_PORT` (default 3001). The bundled templates ship plain HTML in `widgets/out` instead. The MCP server port is `PORT` (default 3000).
- Widget pages are self-contained: plain CSS (inline styles, a `<style>` block, or CSS modules). Don't depend on Tailwind.

## Host / Inspector

- `NITROSTACK_APP_MODE` picks the widget metadata: `universal` (default, set by init; both OpenAI and MCP Apps keys), `openai`, or `mcp-app`.
- MCP Inspector: Streamable HTTP with `MCP_TRANSPORT_TYPE=http MCP_STATELESS=true`, URL `http://localhost:3000/mcp` (no trailing slash), then the **Apps** tab.
- Turn Inspector **Authentication off** for templates without OAuth, or it POSTs `/register` and fails with `Cannot POST /register`.

## Do not

- Scaffold a TypeScript widget package as the source of truth for Python tools.
- Use a widget route that is not a simple name (`calculator-result`, `flight-search-results`).
- Point `_meta.ui.resourceUri` at a non-`ui://` URI.
