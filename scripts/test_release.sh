#!/usr/bin/env bash
# QA-001 test-release channel: final matrix + evidence + known-defect gate.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
PYTHON_BIN="${1:-python}"

FILES=(
  tests/test_release_readiness_regressions.py
  tests/test_package_artifact.py
  tests/test_package_dependencies.py
  tests/test_g0_gate_contract.py
  tests/test_gate_v2.py
  tests/compatibility
)

PYTHONPATH="${ROOT}/src" "${PYTHON_BIN}" -m pytest "${FILES[@]}" -q --tb=short -p no:cacheprovider