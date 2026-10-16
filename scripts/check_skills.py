"""Check every skill against the installed nitrostack SDK.

Every project created by `nitrostack-py init` copies these skills, so a wrong
import here becomes a wrong import in generated code. For each SKILL.md:

- the frontmatter has a unique `name` and a `description`;
- every ```python block compiles;
- every `from nitrostack... import X` names something the SDK has.

Run: python scripts/check_skills.py
"""
from __future__ import annotations

import importlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^```python\n(.*?)^```", re.S | re.M)
IMPORT = re.compile(r"^\s*from (nitrostack[\w.]*) import (\([^)]*\)|[^\n]*)", re.M)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def check(path: pathlib.Path, seen_names: dict) -> list:
    errors = []
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)

    match = FRONTMATTER.match(text)
    fields = dict(re.findall(r"^(\w+):\s*(.+)$", match.group(1), re.M)) if match else {}
    if not fields.get("name") or not fields.get("description"):
        errors.append(f"{rel}: frontmatter needs name and description")
    elif fields["name"] in seen_names:
        errors.append(f"{rel}: name {fields['name']!r} also used by {seen_names[fields['name']]}")
    else:
        seen_names[fields["name"]] = rel

    for i, code in enumerate(FENCE.findall(text), 1):
        try:
            compile(code, f"{rel} python block {i}", "exec")
        except SyntaxError as exc:
            errors.append(f"{rel}: python block {i} doesn't compile: {exc}")
        for mod_name, names in IMPORT.findall(code):
            try:
                mod = importlib.import_module(mod_name)
            except ImportError as exc:
                errors.append(f"{rel}: python block {i}: {exc}")
                continue
            for name in re.split(r"[,\s()]+", names):
                if name and not name.startswith("#") and not hasattr(mod, name):
                    errors.append(f"{rel}: python block {i} imports {name!r} from {mod_name}, which doesn't have it")
    return errors


def main() -> int:
    from importlib.metadata import version

    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    if not skills:
        print("No skills found")
        return 1
    seen: dict = {}
    errors = [e for path in skills for e in check(path, seen)]
    for error in errors:
        print(error)
    print(f"{len(skills)} skills checked against nitrostack {version('nitrostack')}: {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
