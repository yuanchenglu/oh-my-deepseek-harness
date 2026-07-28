#!/usr/bin/env bash
# Repository convenience wrapper. The canonical implementation lives in the
# installed deepseek_harness.installer module and never invokes pip.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if command -v deepseek-harness >/dev/null 2>&1; then
    exec deepseek-harness install "$@"
fi

export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
exec "${PYTHON:-python3}" -m deepseek_harness.cli install "$@"
