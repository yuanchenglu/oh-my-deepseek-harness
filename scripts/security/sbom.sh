#!/usr/bin/env bash
# SEC-001 SBOM generation: build a CycloneDX-light JSON SBOM from pyproject.toml
# dependencies (base + all extras). Wheel/SBOM identity is verified by the
# release checklist; this script produces the machine-readable inventory.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
OUT="${1:-${ROOT}/dist/sbom.json}"

python3 - "$ROOT" "$OUT" <<'PY'
import json
import sys
import tomllib
from pathlib import Path

root = Path(sys.argv[1])
out = Path(sys.argv[2])
pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))

project = pyproject["project"]
deps = list(project.get("dependencies", []))
for extra in project.get("optional-dependencies", {}).values():
    for d in extra:
        if d not in deps:
            deps.append(d)

# Normalize requirement strings -> (name, spec)
components = []
for req in deps:
    name = req.split(";")[0].split("[")[0].strip()
    if " " in name or ">" in name or "<" in name or "=" in name:
        import re
        m = re.match(r"([A-Za-z0-9_.-]+)\s*(.*)", name)
        name, spec = m.group(1), m.group(2).strip()
    else:
        spec = ""
    components.append({
        "name": name,
        "version": spec or "any",
        "purl": f"pkg:pypi/{name.lower()}",
    })

sbom = {
    "bomFormat": "CycloneDX",
    "specVersion": "1.5",
    "component": {
        "name": project["name"],
        "version": project["version"],
        "type": "library",
    },
    "serialNumber": "urn:uuid:00000000-0000-0000-0000-000000000000",
    "dependencies": components,
}

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(sbom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"SBOM written to {out} ({len(components)} components)")
PY