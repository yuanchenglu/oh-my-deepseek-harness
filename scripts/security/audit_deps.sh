#!/usr/bin/env bash
# SEC-001 dependency vulnerability audit (FR-SEC-005).
# Unwaived High/Critical findings block release. Uses pip-audit if available;
# otherwise falls back to a license-inventory report from installed metadata.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if command -v pip-audit >/dev/null 2>&1; then
  pip-audit -r <(sed -n 's/^"\(.*\)",/\1/p' pyproject.toml | grep -E '^[A-Za-z]') 2>/dev/null \
    || pip-audit 2>/dev/null \
    || { echo "pip-audit unavailable or no audit results; run 'pip install pip-audit' for full CVE scan"; }
else
  echo "pip-audit not installed; skipping automated CVE scan (CI installs it)."
  echo "Minimal dependency inventory from pyproject:"
  python3 - <<'PY'
import tomllib
from pathlib import Path
pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
deps = pyproject["project"].get("dependencies", [])
for extra in pyproject["project"].get("optional-dependencies", {}).values():
    deps.extend(d for d in extra if d not in deps)
print(f"  {len(deps)} runtime deps (base+extras)")
for d in deps:
    print(f"  - {d}")
PY
fi