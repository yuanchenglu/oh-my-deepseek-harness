#!/usr/bin/env bash
# DOC-002 new-user rehearsal: prove every CLI command in the lifecycle guides is
# real and that the docs link to existing files. Read-only; no writes to HOME.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
PYTHON_BIN="${1:-python}"

# 1) The docs' own pytest suite (status, links, commands, new-user rehearsal).
PYTHONPATH="${ROOT}/src" "${PYTHON_BIN}" -m pytest \
  "${ROOT}/tests/test_docs.py" -q --tb=short

# 2) Statically verify every `deepseek-harness <sub>` token in the guides
#    resolves to a real subcommand/action via the dispatcher's parser.
PYTHONPATH="${ROOT}/src" "${PYTHON_BIN}" - "${ROOT}" <<'PY'
import argparse
import re
import sys
from pathlib import Path

from deepseek_harness.cli import build_parser

root = Path(sys.argv[1])
parser = build_parser()

# Collect the real subcommand/action surface from the parser itself.
subs = set(parser._subparsers._group_actions[0].choices)
surfaces = {"sub": subs}
for name, subparser in parser._subparsers._group_actions[0].choices.items():
    if name in ("server", "memory", "plan"):
        actions = set(subparser._subparsers._group_actions[0].choices)
        surfaces[f"{name}:actions"] = actions

code_re = re.compile(r"`([^`]+)`")
errors = []
for path in sorted((root / "docs" / "guides").glob("*.md")):
    text = path.read_text(encoding="utf-8")
    for m in code_re.finditer(text):
        token = m.group(1).strip()
        if not (token.startswith("deepseek-harness") or token.startswith("scripts/install.sh")):
            continue
        parts = token.split()
        sub = parts[1] if len(parts) > 1 else ""
        if not sub:
            continue  # bare `deepseek-harness` is the program name, not a subcommand
        if sub not in surfaces["sub"]:
            errors.append(f"{path.name}: unknown subcommand {token!r}")
            continue
        if sub in ("server", "memory", "plan") and len(parts) >= 3:
            action = parts[2]
            if action not in surfaces[f"{sub}:actions"]:
                errors.append(f"{path.name}: unknown action {token!r}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print("test_docs.sh: all guide commands verified against the real CLI parser")
PY

# 3) Every relative markdown link inside the guides must resolve.
#    (Lead by the pytest links test; this adds a filesystem-precise pass.)
"${PYTHON_BIN}" - "${ROOT}" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
errors = []
for path in sorted((root / "docs" / "guides").glob("*.md")):
    text = path.read_text(encoding="utf-8")
    for m in link_re.finditer(text):
        link = m.group(1).strip()
        if link.startswith(("http://", "https://", "#")):
            continue
        target = (path.parent / link.split("#")[0]).resolve()
        if not target.exists():
            errors.append(f"{path.name}: broken link {link!r}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print("test_docs.sh: all guide links resolve")
PY

echo "test_docs.sh: new-user rehearsal passed"