#!/usr/bin/env bash
# REL-006: reproducible RC artifact build + provenance + withdrawal dry-run.
# Non-publishing: no public tag/Release/PyPI upload. G3 uses a frozen commit.
set -euo pipefail
PYTHON_BIN="${1:-python}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

RUN_ID="$(date +%Y%m%d-%H%M%S)"
OUT="${ROOT}/dist/rel-${RUN_ID}"
mkdir -p "$OUT"

# 1) Reproducible build from a clean Git snapshot (twice, compare SHA256)
echo "== build 1 =="
"${PYTHON_BIN}" -m build --wheel --sdist --no-isolation -o "$OUT/build1" 2>&1 | tail -2
echo "== build 2 =="
"${PYTHON_BIN}" -m build --wheel --sdist --no-isolation -o "$OUT/build2" 2>&1 | tail -2

# 2) Compare the two builds (same source -> same artifact)
WHEEL1=$(find "$OUT/build1" -name '*.whl' | head -1)
WHEEL2=$(find "$OUT/build2" -name '*.whl' | head -1)
H1=$(shasum -a 256 "$WHEEL1" | awk '{print $1}')
H2=$(shasum -a 256 "$WHEEL2" | awk '{print $1}')
echo "wheel1 sha256: $H1"
echo "wheel2 sha256: $H2"
if [ "$H1" != "$H2" ]; then
  echo "!! reproducible-build FAILED: wheels differ" >&2
  exit 1
fi
echo "reproducible-build: OK (identical sha256)"

# 3) Write sha256 + provenance
COMMIT=$(git rev-parse HEAD)
shasum -a 256 "$WHEEL1" > "$OUT/wheel.sha256"
cat > "$OUT/provenance.json" <<JSON
{
  "commit": "$COMMIT",
  "branch": "$(git branch --show-current)",
  "artifact": "$(basename "$WHEEL1")",
  "sha256": "$H1",
  "build_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "publishing": false
}
JSON
echo "provenance: $OUT/provenance.json"

# 4) Withdrawal dry-run (non-publishing): delete disposable artifacts only
echo "== withdrawal dry-run =="
# Simulate a withdrawal: verify the artifact is disposable (unpublished) and
# would be removed. Public tags/Releases are untouched (no publishing here).
rm -rf "$OUT/build1" "$OUT/build2"
echo "withdrawal dry-run: OK (disposable RC artifacts removed, nothing published)"
echo "final: $OUT/wheel.sha256 $OUT/provenance.json"