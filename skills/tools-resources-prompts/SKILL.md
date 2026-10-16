---
name: nitrostack-python-tools-resources-prompts
description: Define MCP tools, resources, and prompts in NitroStack Python with Pydantic schemas and ExecutionContext.
---

## When to Use

Defining, editing, or validating tools, resources, or prompts on a **Python** NitroStack server. Use Pydantic `BaseModel`, not Zod. Caching, rate limits, and background tasks are in the runtime-features skill.

## Tools

Decorate **async methods on an `@injectable` class** listed in the module's `controllers`. Signature is `(self, input: Model, context: ExecutionContext)`; `input` is an instance of `input_schema`.

`@tool` options: `name`, `description`, `input_schema` (required), plus optional `title`, `output_schema`, `annotations` (`ToolAnnotations`), `task_support`, `visibility`, `examples` (`ToolExamples`), `invocation`, `metadata`.

```python
from typing import Literal
from pydantic import BaseModel, Field
from nitrostack import injectable, tool, widget, ToolAnnotations, ToolExamples, ExecutionContext

class CalculateInput(BaseModel):
    operation: Literal["add", "subtract", "multiply", "divide"] = Field(description="The operation to perform")
    a: float = Field(description="First number")
    b: float = Field(description="Second number")

class CalculateOutput(BaseModel):
    result: float
    expression: str

@injectable()
class CalculatorTools:
    @tool(
        name="calculate",
        title="Calculate",
        description="Perform basic arithmetic calculations",
        input_schema=CalculateInput,
        output_schema=CalculateOutput,
        annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True),
        examples=ToolExamples(
            input={"operation": "add", "a": 5, "b": 3},
            output={"result": 8, "expression": "5 + 3 = 8"},
        ),
    )
    @widget("calculator-result")
    async def calculate(self, input: CalculateInput, context: ExecutionContext) -> dict:
        context.logger.info(f"{input.operation} {input.a} {input.b}")
        result = input.a + input.b
        return {"result": result, "expression": f"{input.a:g} + {input.b:g} = {result:g}"}
```

- Always pass `examples`: client LLMs use them to get argument shapes right.
- A tool with no arguments still needs an input model. Use an empty subclass (`class NoInput(BaseModel): pass`), never `BaseModel` itself, which fails at startup.
- `visibility="hidden"` keeps a tool callable but out of `tools/list`.
- Raise an exception to return an MCP error to the client.
- Stack `@initial_tool` (before or after `@tool`) to auto-invoke on client connect.
- Inspector sends empty strings for unused optionals; use Pydantic `field_validator(..., mode="before")` to coerce `""` to defaults when needed.
- Keep database queries and business logic in a service (`providers`), injected into the controller.

## Resources

Resource handlers take `(self, context)`. List the class on the feature module `controllers`.

```python
from nitrostack import injectable, resource, ResourceAnnotations, ExecutionContext

@injectable()
class FlightResources:
    @resource(
        uri="flight://popular-routes",
        name="Popular Flight Routes",
        description="Information about popular routes and pricing",
        mime_type="application/json",
        annotations=ResourceAnnotations(audience=["assistant"], priority=1.0),
    )
    async def popular_routes(self, context: ExecutionContext) -> dict:
        return {"routes": [{"from": "JFK", "to": "LHR"}]}
```

## Prompts

Prompt handlers take `(self, args: dict, context)` and return a string or a list of `PromptMessage`. Declare arguments with `PromptArgument` so clients can ask for them.

```python
from typing import List
from nitrostack import injectable, prompt, PromptArgument, PromptMessage, ExecutionContext

@injectable()
class FlightPrompts:
    @prompt(
        name="flight_search_assistant",
        description="Help users search for flights and book holds.",
        arguments=[PromptArgument(name="destination", description="Where to fly", required=True)],
    )
    async def flight_search_assistant(self, args: dict, context: ExecutionContext) -> List[PromptMessage]:
        return [PromptMessage(role="user", content=f"Find flights to {args['destination']} with search_flights.")]
```

## File uploads in tools (base64)

Clients often send uploads as base64 strings in the tool input schema:

```python
import base64
import os
import re
from pathlib import Path
from pydantic import BaseModel, Field
from nitrostack import injectable, tool, ExecutionContext

class FileUploadInput(BaseModel):
    file_name: str = Field(description="Original file name")
    file_content: str = Field(description="Base64 or data-URL encoded content")

UPLOAD_DIR = Path(os.getcwd()) / "uploads"

def decode_base64_file(content: str) -> bytes:
    data_url_match = re.match(r"^data:[^;]+;base64,(.+)$", content)
    raw_data = data_url_match.group(1) if data_url_match else content
    return base64.b64decode(raw_data)

@injectable()
class FileTools:
    @tool(name="upload_document", description="Save uploaded file securely", input_schema=FileUploadInput)
    async def upload_document(self, input: FileUploadInput, context: ExecutionContext) -> dict:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        safe_filename = Path(input.file_name).name
        destination = (UPLOAD_DIR / safe_filename).resolve()
        if not str(destination).startswith(str(UPLOAD_DIR.resolve())):
            raise ValueError("Invalid file path (path traversal detected).")
        file_bytes = decode_base64_file(input.file_content)
        destination.write_bytes(file_bytes)
        return {"success": True, "saved_path": str(destination), "bytes": len(file_bytes)}
```

## Do not

- Use `z.object` / Zod `inputSchema`.
- Register a bare function as a tool without a controller class unless you are matching an existing example in this repo.
- Invent Nest-style `@Controller('prefix')`. Python tools use the `name=` string as the MCP tool name.
- Put `@cache` on a tool method: it cannot key on the Pydantic input. Cache a service method instead (runtime-features skill).
- Write unvalidated file paths directly to disk without path traversal checks.
