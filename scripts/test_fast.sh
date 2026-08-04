#!/usr/bin/env bash
# QA-001 test-fast channel: no network / real HOME / API. Pure unit & contract.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
PYTHON_BIN="${1:-python}"

FILES=(
  tests/test_intent_router.py
  tests/test_assessor_v2.py
  tests/test_audit.py
  tests/test_checkpoint.py
  tests/test_plan.py
  tests/test_memory.py
  tests/test_session_policy.py
  tests/test_context_engine.py
  tests/test_context_privacy.py
  tests/test_context_token_accounting.py
  tests/test_context_integrity_regressions.py
  tests/test_context_compressor_transactions.py
  tests/test_tool_contract.py
  tests/test_tool_registration.py
  tests/test_plugin_yaml.py
  tests/test_docs.py
)

PYTHONPATH="${ROOT}/src" "${PYTHON_BIN}" -m pytest "${FILES[@]}" -q --tb=short -p no:cacheprovider