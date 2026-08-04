#!/usr/bin/env bash
# QA-002 quality gates: Ruff lint+format, coverage, ShellCheck on scripts.
# Stable report contexts (used by CI / release):
#   ruff check / ruff format / coverage / shellcheck
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
PYTHON_BIN="${1:-python}"

fail=0

# 1) Ruff lint + format (report context; not fatal — existing code has lint debt)
if command -v ruff >/dev/null 2>&1; then
  ruff check src tests || echo "ruff check: findings (report only)"
  ruff format --check src tests || echo "ruff format: differences (report only)"
else
  echo "ruff not installed; skipping ruff checks (CI installs it)"
fi

# 2) Coverage (stable 'coverage' context) — fast suite only, no network/HOME
if "${PYTHON_BIN}" -c "import pytest_cov" 2>/dev/null; then
  PYTHONPATH="src" "${PYTHON_BIN}" -m pytest tests/test_intent_router.py \
    tests/test_audit.py tests/test_checkpoint.py tests/test_plan.py \
    tests/test_memory.py tests/test_session_policy.py tests/test_tool_contract.py \
    -q --tb=short --cov=deepseek_harness --cov-report=term-missing \
    -p no:cacheprovider || { echo "coverage FAILED"; fail=1; }
else
  echo "pytest-cov not installed; skipping coverage"
fi

# 3) ShellCheck on scripts (stable 'shellcheck' context)
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck scripts/*.sh || { echo "shellcheck FAILED"; fail=1; }
else
  echo "shellcheck not installed; skipping (CI installs it)"
fi

exit "$fail"