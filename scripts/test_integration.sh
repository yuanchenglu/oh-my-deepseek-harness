#!/usr/bin/env bash
# QA-001 test-integration channel: controlled processes/artifacts.
# Server E2E, install E2E, lifecycle, doctor, supervisor, context properties.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
PYTHON_BIN="${1:-python}"

FILES=(
  tests/test_harness_server.py
  tests/test_server_process.py
  tests/test_installer_e2e.py
  tests/test_latest_reminder.py
  tests/test_reasoning_effort.py
  tests/test_lifecycle.py
  tests/test_lifecycle_security.py
  tests/test_doctor.py
  tests/test_supervisor_safety.py
  tests/test_subagent_watch.py
  tests/test_learner.py
  tests/test_context_properties.py
)

PYTHONPATH="${ROOT}/src" "${PYTHON_BIN}" -m pytest "${FILES[@]}" -q --tb=short -p no:cacheprovider