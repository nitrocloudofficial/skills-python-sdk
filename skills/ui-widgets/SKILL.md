---
name: nitrostack-python-ui-widgets
description: Python NitroStack MCP Apps widgets — @widget, widgets/out HTML, WidgetOptions, and preview.
---

## When to Use

Attaching UI to a Python tool result (Calculator, Pizzaz, flight-booking). Not `@nitrostack/ui` npm widgets.

## Associate a widget with a tool

```python
from nitrostack import tool, widget, WidgetOptions, WidgetCsp

@tool(name="calculate", description="...", input_schema=CalculateInput)
@widget("calculator-result")
async def calculate(self, input: CalculateInput, context: ExecutionContext) -> dict:
    return {"result": ..., "expression": ...}
```

Or with CSP / border:

```python
@widget(WidgetOptions(
    route="pizza-map",
    prefers_border=True,
    csp=WidgetCsp(
        resource_domains=["https://api.mapbox.com", ...],
        connect_domains=["https://api.mapbox.com"],
    ),
))
```

`nitrostack-py init` and `ensure_python_widgets` write `widgets/out/{route}.html` plus `widgets/preview.html`. Routes are scraped from `@widget("...")` and `WidgetOptions(route="...")`.

Return JSON/`dict` from the tool; the widget HTML reads `structuredContent` / injected tool data. Do not return a React tree from Python.

## Files

- `widgets/out/<route>.html` — page the MCP host loads (`ui://widget/<route>.html`).
- `widgets/preview.html` — static preview.
- Optional `src/widgets/` Next app in some templates for local widget `npm run dev` (port `WIDGETS_DEV_PORT`, default 3001). MCP server port is `PORT` (default 3000).

## Host / Inspector

`NITROSTACK_APP_MODE=universal` (set by init). Streamable HTTP: `MCP_TRANSPORT_TYPE=http` (and `MCP_STATELESS=true` when using the inspector flow documented in init next-steps).

## Do not

- Scaffold a TypeScript widget package as the source of truth for Python tools.
- Use a widget route that is not a simple name (`calculator-result`, `flight-search-results`).
- Point `_meta.ui.resourceUri` at a non-`ui://` URI.
