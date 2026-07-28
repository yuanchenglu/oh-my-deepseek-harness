#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${1:-python}"
ROOT="$(git rev-parse --show-toplevel)"
RESULTS_DIR="${QA_ARTIFACT_RESULTS_DIR:-${ROOT}/test-results/artifact}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/qa-art-001.XXXXXX")"
SOURCE="${WORK}/source"
WHEELHOUSE="${WORK}/wheelhouse"
VENV="${WORK}/venv"
HOME_DIR="${WORK}/home"
PROBE="${WORK}/probe"
FAKE_BIN="${WORK}/fake-bin"
DATA_ROOT="${HOME_DIR}/.hermes/oh-my-deepseek-harness"
DB_PATH="${DATA_ROOT}/data/harness.db"
MEMORIES_DIR="${HOME_DIR}/.hermes/memories"
CONSOLE="${VENV}/bin/deepseek-harness"
VENV_PY="${VENV}/bin/python"

mkdir -p "${RESULTS_DIR}" "${SOURCE}" "${WHEELHOUSE}" "${HOME_DIR}" "${PROBE}" "${FAKE_BIN}"

cleanup() {
  if [[ -x "${CONSOLE}" ]]; then
    HOME="${HOME_DIR}" USERPROFILE="${HOME_DIR}" \
    HARNESS_DATA_ROOT="${DATA_ROOT}" HARNESS_DB_PATH="${DB_PATH}" \
    HARNESS_MEMORIES_DIR="${MEMORIES_DIR}" HARNESS_HOST="127.0.0.1" \
    HARNESS_PORT="${PORT:-8200}" "${CONSOLE}" server stop \
      --data-root "${DATA_ROOT}" --json >/dev/null 2>&1 || true
  fi
  rm -rf "${WORK}"
}
trap cleanup EXIT

# Build only from a clean Git snapshot. The working tree is never used as a build input.
git -C "${ROOT}" archive --format=tar HEAD >"${WORK}/source.tar"
tar -xf "${WORK}/source.tar" -C "${SOURCE}"
"${PYTHON_BIN}" -m pip wheel --no-deps --wheel-dir "${WHEELHOUSE}" "${SOURCE}" \
  >"${RESULTS_DIR}/build.log" 2>&1

mapfile -t WHEELS < <(find "${WHEELHOUSE}" -maxdepth 1 -type f -name 'oh_my_deepseek_harness-3.0.0b1-*.whl' -print)
if [[ "${#WHEELS[@]}" -ne 1 ]]; then
  printf 'expected exactly one wheel, found %s\n' "${#WHEELS[@]}" >&2
  exit 1
fi
WHEEL="${WHEELS[0]}"
cp "${WHEEL}" "${RESULTS_DIR}/"
sha256sum "${WHEEL}" >"${RESULTS_DIR}/wheel.sha256"

"${PYTHON_BIN}" - "${WHEEL}" "${RESULTS_DIR}/wheel-inventory.json" <<'PY'
import json
import sys
import zipfile
from pathlib import Path

wheel = Path(sys.argv[1])
out = Path(sys.argv[2])
with zipfile.ZipFile(wheel) as archive:
    names = sorted(archive.namelist())
required = {
    "deepseek_harness/cli.py",
    "deepseek_harness/doctor.py",
    "deepseek_harness/installer.py",
    "deepseek_harness/lifecycle.py",
    "deepseek_context/plugin.py",
    "harness_server/runtime.py",
    "harness_server/server.py",
    "harness_server/supervisor.py",
}
missing = sorted(required - set(names))
assert not missing, missing
assert not any(name.startswith(("plugins/", "mcp/", "tests/")) for name in names)
out.write_text(
    json.dumps({"wheel": wheel.name, "file_count": len(names), "files": names}, indent=2),
    encoding="utf-8",
)
PY

"${PYTHON_BIN}" -m venv "${VENV}"
"${VENV_PY}" -m pip install --upgrade pip >"${RESULTS_DIR}/venv-pip.log" 2>&1
"${VENV_PY}" -m pip install "${WHEEL}[all]" >"${RESULTS_DIR}/install-wheel.log" 2>&1

cat >"${FAKE_BIN}/hermes" <<'SH'
#!/usr/bin/env sh
printf 'Hermes 0.19.0\n'
SH
chmod 0755 "${FAKE_BIN}/hermes"
PORT="$(${VENV_PY} - <<'PY'
import socket
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)"

export HOME="${HOME_DIR}"
export USERPROFILE="${HOME_DIR}"
export HARNESS_DATA_ROOT="${DATA_ROOT}"
export HARNESS_DB_PATH="${DB_PATH}"
export HARNESS_MEMORIES_DIR="${MEMORIES_DIR}"
export HARNESS_IMPORT_MEMORIES=0
export HARNESS_HOST=127.0.0.1
export HARNESS_PORT="${PORT}"
export DEEPSEEK_API_KEY=fake-qa-art-001-key
export PYTHONNOUSERSITE=1
export PYTHONPATH=
export PATH="${FAKE_BIN}:${VENV}/bin:${PATH}"

cd "${PROBE}"

# Prove all imports and console metadata come from the temporary wheel environment.
"${VENV_PY}" - "${ROOT}" "${SOURCE}" "${VENV}" "${RESULTS_DIR}/import-probe.json" <<'PY'
import importlib.metadata
import json
import sys
from pathlib import Path

repository = Path(sys.argv[1]).resolve()
archived_source = Path(sys.argv[2]).resolve()
venv = Path(sys.argv[3]).resolve()
out = Path(sys.argv[4])

import deepseek_context
import deepseek_harness
import harness_server
import deepseek_harness.cli
import deepseek_harness.doctor
import deepseek_harness.installer
import deepseek_harness.lifecycle

modules = (
    deepseek_harness,
    deepseek_context,
    harness_server,
    deepseek_harness.cli,
    deepseek_harness.doctor,
    deepseek_harness.installer,
    deepseek_harness.lifecycle,
)
locations = {}
for module in modules:
    location = Path(module.__file__).resolve()
    assert repository != location and repository not in location.parents, (module.__name__, location)
    assert archived_source != location and archived_source not in location.parents, (module.__name__, location)
    assert venv in location.parents, (module.__name__, location)
    locations[module.__name__] = str(location.relative_to(venv))

for entry in sys.path:
    if not entry:
        continue
    resolved = Path(entry).resolve()
    assert resolved != repository and repository not in resolved.parents
    assert resolved != archived_source and archived_source not in resolved.parents

distribution = importlib.metadata.distribution("oh-my-deepseek-harness")
assert distribution.version == "3.0.0b1"
out.write_text(
    json.dumps(
        {
            "distribution_version": distribution.version,
            "modules": locations,
            "python": sys.version,
            "sys_path": sys.path,
        },
        indent=2,
        sort_keys=True,
    ),
    encoding="utf-8",
)
PY

"${CONSOLE}" install --dry-run --json >"${RESULTS_DIR}/install-dry-run.json"
[[ ! -e "${DATA_ROOT}" ]]
"${CONSOLE}" install --json >"${RESULTS_DIR}/install.json"

set +e
"${CONSOLE}" doctor --json >"${RESULTS_DIR}/doctor.json"
DOCTOR_RC=$?
set -e
PY_MINOR="$(${VENV_PY} -c 'import sys; print(sys.version_info.minor)')"
if [[ "${PY_MINOR}" == "10" ]]; then
  [[ "${DOCTOR_RC}" -eq 5 ]]
else
  [[ "${DOCTOR_RC}" -eq 0 ]]
fi

"${VENV_PY}" - "${PORT}" "${RESULTS_DIR}/server-smoke.json" <<'PY'
import json
import sys
import httpx
from pathlib import Path

port = int(sys.argv[1])
out = Path(sys.argv[2])
base = f"http://127.0.0.1:{port}"
with httpx.Client(timeout=5, trust_env=False) as client:
    health = client.get(f"{base}/health")
    ready = client.get(f"{base}/ready")
    version = client.get(f"{base}/version")
    tool = client.post(f"{base}/memory/tag", json={"content": "must not expose secrets"})
for response in (health, ready, version, tool):
    assert response.status_code == 200, (response.request.url, response.status_code, response.text)
payload = {
    "health": health.json(),
    "ready": ready.json(),
    "version": version.json(),
    "memory_tag": tool.json(),
}
assert payload["health"]["status"] == "ok"
assert payload["ready"]["status"] == "ready"
assert payload["version"]["version"] == "3.0.0b1"
assert payload["memory_tag"]["layer"] == "constraint"
out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
PY

"${CONSOLE}" upgrade --dry-run --json >"${RESULTS_DIR}/upgrade-dry-run.json"
"${CONSOLE}" upgrade --json >"${RESULTS_DIR}/upgrade.json"
"${VENV_PY}" - "${RESULTS_DIR}/install.json" "${RESULTS_DIR}/upgrade.json" <<'PY'
import json
import sys
from pathlib import Path
install = json.loads(Path(sys.argv[1]).read_text())
upgrade = json.loads(Path(sys.argv[2]).read_text())
assert install["server_pid"] == upgrade["server_pid"]
assert upgrade["state"] == "up_to_date"
assert upgrade["changed"] is False
assert upgrade["ready"] is True
PY

"${CONSOLE}" uninstall --json >"${RESULTS_DIR}/uninstall.json"
"${VENV_PY}" - "${RESULTS_DIR}/uninstall.json" "${DATA_ROOT}" "${DB_PATH}" <<'PY'
import importlib.metadata
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
data_root = Path(sys.argv[2])
db_path = Path(sys.argv[3])
assert payload["state"] == "uninstalled"
assert payload["pip_uninstall_command"] == "python -m pip uninstall oh-my-deepseek-harness"
assert data_root.is_dir()
assert (data_root / "config" / "config.yaml").is_file()
assert db_path.is_file()
assert importlib.metadata.version("oh-my-deepseek-harness") == "3.0.0b1"
import deepseek_harness
assert deepseek_harness.__file__
PY

# Distribution removal is explicit test-harness work in the temporary venv, never product CLI work.
"${VENV_PY}" -m pip uninstall -y oh-my-deepseek-harness >"${RESULTS_DIR}/explicit-pip-uninstall.log" 2>&1
if "${VENV_PY}" -c 'import deepseek_harness' >/dev/null 2>&1; then
  echo "distribution import still succeeds after explicit pip uninstall" >&2
  exit 1
fi

cat >"${RESULTS_DIR}/junit.xml" <<XML
<?xml version="1.0" encoding="utf-8"?>
<testsuite name="qa-art-001" tests="1" failures="0" errors="0" skipped="0">
  <testcase classname="artifact.lifecycle" name="external_wheel_full_lifecycle"/>
</testsuite>
XML

printf 'QA-ART-001 external artifact lifecycle passed with Python %s\n' "${PY_MINOR}"
