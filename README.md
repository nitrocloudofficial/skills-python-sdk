# NitroStack Python SDK agent skills

Skill files copied into generated projects by `nitrostack-py init` (and refreshed by `nitrostack-py upgrade`).

Layout: each subdirectory of `skills/` is one skill (typically a `SKILL.md`). The CLI clones this repository and copies those directories into `.cursor/skills`, `.claude/skills`, `.copilot/skills`, and the other supported agent folders.

Bump `package.json` `version` when skill content changes so `upgrade` can detect a newer release.
