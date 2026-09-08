---
name: nitrostack-python-tools-resources-prompts
description: Define MCP tools, resources, and prompts in NitroStack Python with Pydantic schemas and ExecutionContext.
---

## When to Use

Defining, editing, or validating tools, resources, or prompts on a **Python** NitroStack server. Use Pydantic `BaseModel`, not Zod.

## Tools

Decorate **async methods on an `@injectable` class** (listed in the module’s `controllers`). Signature is `(self, input: Model, context: ExecutionContext)`.

```python
from nitrostack import injectable, tool, widget, ExecutionContext
from pydantic import BaseModel, Field
from typing import Literal

class CalculateInput(BaseModel):
    operation: Literal["add", "subtract", "multiply", "divide"] = Field(description="The operation to perform")
    a: float = Field(description="First number")
    b: float = Field(description="Second number")

@injectable()
class CalculatorTools:
    @tool(
        name="calculate",
        description="Perform basic arithmetic calculations",
        input_schema=CalculateInput,
        output_schema=CalculateOutput,  # optional Pydantic model
    )
    @widget("calculator-result")
    async def calculate(self, input: CalculateInput, context: ExecutionContext) -> dict:
        context.logger.info(f"{input.operation} {input.a} {input.b}")
        return {"result": input.a + input.b, ...}
```

`@tool` keyword args: `name`, `description`, `input_schema` (required), plus optional `title`, `output_schema`, `annotations`, `task_support`, `visibility`, `examples` (`ToolExamples`), `invocation`, `metadata`.

Stack `@initial_tool` (before or after `@tool`) to auto-invoke on client connect.

Inspector sends empty strings for unused optionals; use Pydantic `field_validator(..., mode="before")` to coerce `""` to defaults when needed.

## Resources

```python
from nitrostack import injectable, resource, ExecutionContext

@injectable(deps=[DuffelService])
class FlightResources:
    def __init__(self, service: DuffelService):
        self.service = service

    @resource(
        uri="flight://popular-routes",
        name="Popular Flight Routes",
        description="Information about popular routes and pricing",
        mime_type="application/json",
    )
    async def popular_routes(self, context: ExecutionContext) -> dict:
        return {"routes": [...]}
```

List the class on the feature module `controllers`.

## Prompts

```python
from nitrostack import injectable, prompt, ExecutionContext

@prompt(
    name="flight_search_assistant",
    description="Help users search for flights and book holds.",
)
async def flight_search_assistant(self, args: dict, context: ExecutionContext) -> str:
    return "Use search_flights and search_airports, then create an order hold."
```

## Do not

- Use `z.object` / Zod `inputSchema`.
- Register a bare function as a tool without a controller class unless you are matching an existing example in this repo.
- Invent Nest-style `@Controller('prefix')` — Python tools use the `name=` string as the MCP tool name.
