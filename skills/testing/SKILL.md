---
name: nitrostack-python-testing
description: Test NitroStack Python tools, resources, and prompts in-process with NitroTestingModule and pytest.
---

## When to Use

Writing or running tests for a Python NitroStack server, or checking a tool change before connecting a client.

## In-process harness

`NitroTestingModule.create(AppModule)` boots the app's DI container and registries without a transport or subprocess.

```python
import asyncio
from nitrostack import DIContainer, NitroTestingModule
from app_module import AppModule

def test_calculate():
    async def run():
        harness = await NitroTestingModule.create(AppModule)
        result = await harness.call_tool("calculate", {"operation": "add", "a": 5, "b": 3})
        assert result["result"] == 8
        assert "routes" in await harness.read_resource("flight://popular-routes")
        messages = await harness.get_prompt("flight_search_assistant", {"destination": "Oslo"})
        assert "Oslo" in str(messages)

    DIContainer.reset()
    asyncio.run(run())
```

- `call_tool(name, args)` takes the arguments as an MCP client sends them (a flat dict, not the Pydantic model) and returns the decoded result: JSON is parsed.
- Errors come back as their message string, not as exceptions. Assert on the text: `assert "Access denied" in str(result)`.
- A tool with no arguments is called with `{}`.
- Singletons live for the process. Call `DIContainer.reset()` between tests (an autouse pytest fixture works well) so state from one test doesn't leak into the next.
- Set environment variables with pytest's `monkeypatch.setenv` before `create`; the process environment wins over `.env`.

## Running

```bash
pip install pytest   # or: uv add --dev pytest
pytest
```

Keep tests in `tests/`, and make test inputs match what the tools expect: real IDs, exact ISO dates, names the service can resolve.

## Do not

- Start the HTTP server or a subprocess to test tool logic.
- Call controller methods directly; that skips guards, pipes and validation.
