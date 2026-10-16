# NitroStack Python SDK agent skills

Skill files copied into generated projects by `nitrostack-py init` (and refreshed by `nitrostack-py upgrade`).

Layout: each subdirectory of `skills/` is one skill (typically a `SKILL.md`). The CLI clones this repository and copies those directories into `.cursor/skills`, `.claude/skills`, `.copilot/skills`, and the other supported agent folders.

| Skill | Covers |
|---|---|
| `mcp-app-architecture` | `main.py`, `AppModule`, feature modules, DI, services |
| `tools-resources-prompts` | `@tool`, `@resource`, `@prompt`, Pydantic schemas, examples |
| `middleware-pipeline` | Guards, pipes, middleware, interceptors, exception filters |
| `auth-security` | API keys, JWT, OAuth 2.1, scopes |
| `config-environment` | `ConfigService`, `.env` precedence, SDK variables |
| `runtime-features` | Caching, rate limits, MCP tasks, events, health checks |
| `transports-cli` | stdio/http/dual, protocol era, `nitrostack-py` commands |
| `testing` | `NitroTestingModule` and pytest |
| `ui-widgets` | `@widget`, `widgets/out`, app modes, Inspector |

Every project created by `init` clones `main`, so a change lands in new projects as soon as it merges.

## Checks

`scripts/check_skills.py` runs in CI against the latest `nitrostack` on PyPI. It checks that every skill has a unique `name` and a `description`, every `python` block compiles, and every `from nitrostack... import` names something the SDK has. Run it locally with:

```bash
uv run --no-project --with nitrostack python scripts/check_skills.py
# or against a local SDK checkout:
uv run --no-project --with-editable ../nitrostack-python-sdk python scripts/check_skills.py
```

Bump `package.json` `version` when skill content changes so `upgrade` can detect a newer release.
