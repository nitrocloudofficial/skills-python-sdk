---
name: nitrostack-python-tools-resources-prompts
description: Guidelines and patterns for defining Tools, Resources, Prompts, Caching, Rate Limiting, Tasks, and File Uploads in NitroStack Python MCP servers.
---

## When to Use
Use this skill when defining, validating, or optimizing Tools (`@tool`), Resources (`@resource`), and Prompts (`@prompt`) on a NitroStack Python MCP server using Pydantic schemas, execution context, caching, rate limiting, and background tasks.

---

## 1. Defining Tools (`@tool`)

An MCP tool exposes a callable function to AI clients. Decorate async methods on an `@injectable` controller class with `@tool`.

### Tool Options:
* `name` (required): Unique snake_case string identifier.
* `description` (required): Clear description guiding the LLM when to invoke the tool.
* `input_schema` (required): Pydantic `BaseModel` class defining input schema.
* `output_schema` (optional): Pydantic model validating output payload structure.
* `annotations` (optional): `ToolAnnotations(destructive_hint=..., read_only_hint=..., idempotent_hint=..., open_world_hint=...)`.
* `task_support` (optional): `"forbidden"`, `"optional"`, or `"required"` for long-running task processing.
* `visibility` (optional): `"visible"` or `"hidden"`.

### Example:
```python
from nitrostack import injectable, tool, initial_tool, ToolAnnotations, ExecutionContext
from pydantic import BaseModel, Field
from typing import Literal

class WeatherInput(BaseModel):
    city: str = Field(description="City name, e.g., San Francisco")
    unit: Literal["celsius", "fahrenheit"] = Field(default="celsius", description="Temperature unit")

class WeatherOutput(BaseModel):
    temperature: float
    condition: str

@injectable()
class WeatherTools:
    @tool(
        name="get_current_weather",
        description="Get current weather conditions for a given city.",
        input_schema=WeatherInput,
        output_schema=WeatherOutput,
        annotations=ToolAnnotations(read_only_hint=True),
    )
    @initial_tool  # Optional: Auto-invoked when client initializes/connects
    async def get_weather(self, input: WeatherInput, context: ExecutionContext) -> dict:
        context.logger.info(f"Fetching weather for {input.city}")
        return {"temperature": 21.5, "condition": "Sunny"}
```

---

## 2. Tool Policies: Caching (`@cache`) & Rate Limiting (`@rate_limit`)

Control performance and throttle requests with method decorators from `nitrostack`.

### Caching (`@cache`):
Caches method outputs for a given TTL in seconds. Skips `ExecutionContext` when building cache keys.
```python
from nitrostack import injectable, tool, cache, ExecutionContext
from pydantic import BaseModel

class StatusInput(BaseModel):
    system_id: str

@injectable()
class DiagnosticTools:
    @tool(name="get_system_status", description="Get diagnostic metrics", input_schema=StatusInput)
    @cache(ttl=60)  # Caches result for 60 seconds
    async def get_status(self, input: StatusInput, context: ExecutionContext) -> dict:
        return {"system_id": input.system_id, "healthy": True}
```

### Rate Limiting (`@rate_limit`):
Restricts tool execution frequency to a maximum number of calls within a time window (in seconds).
```python
from nitrostack import injectable, tool, rate_limit, ExecutionContext
from pydantic import BaseModel

class DiagnosticInput(BaseModel):
    deep_scan: bool = False

@injectable()
class MaintenanceTools:
    @tool(name="run_diagnostics", description="Runs heavy diagnostics", input_schema=DiagnosticInput)
    @rate_limit(max=5, window=60)  # Maximum 5 calls per 60 seconds
    async def run_diagnostics(self, input: DiagnosticInput, context: ExecutionContext) -> dict:
        return {"scan_complete": True}
```

---

## 3. Asynchronous Background Tasks

For long-running tools, set `task_support="optional"` or `"required"` and use `context.task` for progress reporting and cancellation checks.

```python
import asyncio
from nitrostack import injectable, tool, ExecutionContext
from pydantic import BaseModel, Field

class DataProcessingInput(BaseModel):
    dataset_url: str = Field(description="URL of dataset to process")

@injectable()
class DataPipelineTools:
    @tool(
        name="process_large_dataset",
        description="Processes large dataset asynchronously",
        input_schema=DataProcessingInput,
        task_support="optional",  # or "required"
    )
    async def process_dataset(self, input: DataProcessingInput, context: ExecutionContext) -> dict:
        total_steps = 5
        for step in range(1, total_steps + 1):
            # Check if client cancelled the task
            if context.task:
                context.task.throw_if_cancelled()
                context.task.update_progress(f"Processing step {step}/{total_steps}...")

            await asyncio.sleep(1)  # Simulate processing chunk

        return {"status": "completed", "dataset": input.dataset_url}
```

---

## 4. Handling File Uploads in Tools (Base64)

NitroStack tools receive client file uploads as base64-encoded strings within Pydantic schemas.

### 1. Define Input Schema:
```python
from pydantic import BaseModel, Field

class FileUploadInput(BaseModel):
    file_name: str = Field(description="Original file name, e.g., document.pdf")
    file_type: str = Field(description="MIME type, e.g., application/pdf")
    file_content: str = Field(description="Base64 encoded file content")
```

### 2. Universal Base64 Decoder & Secure File Storage:
```python
import base64
import os
import re
from pathlib import Path
from nitrostack import injectable, tool, ExecutionContext

UPLOAD_DIR = Path(os.getcwd()) / "uploads"

def decode_base64_file(content: str) -> bytes:
    """Decodes Data URL or raw base64 string into bytes."""
    data_url_match = re.match(r"^data:[^;]+;base64,(.+)$", content)
    raw_data = data_url_match.group(1) if data_url_match else content
    return base64.b64decode(raw_data)

@injectable()
class FileTools:
    @tool(name="upload_document", description="Save uploaded file securely", input_schema=FileUploadInput)
    async def upload_document(self, input: FileUploadInput, context: ExecutionContext) -> dict:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Prevent directory traversal attacks
        safe_filename = Path(input.file_name).name
        destination = (UPLOAD_DIR / safe_filename).resolve()
        if not str(destination).startswith(str(UPLOAD_DIR.resolve())):
            raise ValueError("Invalid file path (path traversal detected).")

        file_bytes = decode_base64_file(input.file_content)
        destination.write_bytes(file_bytes)

        context.logger.info(f"Saved file {safe_filename} ({len(file_bytes)} bytes)")
        return {"success": True, "saved_path": str(destination), "bytes": len(file_bytes)}
```

---

## 5. Defining Resources (`@resource`)

Resources expose data or files at custom URI schemes that AI clients can inspect.

```python
from nitrostack import injectable, resource, ResourceAnnotations, ExecutionContext

@injectable()
class ServerResources:
    @resource(
        uri="server://config",
        name="Server Configuration",
        description="System configuration parameters",
        mime_type="application/json",
        annotations=ResourceAnnotations(audience=["assistant"], priority=1.0),
    )
    async def get_config(self, context: ExecutionContext) -> dict:
        return {"env": "production", "debug": False}
```

---

## 6. Defining Prompts (`@prompt`)

Prompts expose parameterized prompt templates to guide LLM interactions.

```python
from nitrostack import injectable, prompt, PromptArgument, ExecutionContext

@injectable()
class AssistantPrompts:
    @prompt(
        name="code_review",
        description="Review code according to security and style guidelines",
        arguments=[
            PromptArgument(name="language", description="Target language (e.g. Python)", required=True),
            PromptArgument(name="code", description="Source code snippet", required=True),
        ],
    )
    async def code_review_prompt(self, arguments: dict, context: ExecutionContext) -> list:
        lang = arguments.get("language", "Python")
        code = arguments.get("code", "")
        return [
            {
                "role": "user",
                "content": f"You are a senior {lang} engineer. Review this code for bugs and security:\n\n{code}",
            }
        ]
```

---

## Do Not
- Do not use Zod (`z.object`) — use Pydantic `BaseModel`.
- Do not forget `context: ExecutionContext` parameter on `@tool`, `@resource`, and `@prompt` methods.
- Do not write unvalidated file paths directly to disk without path traversal checks.
