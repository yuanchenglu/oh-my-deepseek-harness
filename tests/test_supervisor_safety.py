"""RUN-002 fail-closed process ownership and state tests."""

from __future__ import annotations

import signal
from pathlib import Path

import pytest

import harness_server.runtime as runtime_module
import harness_server.supervisor as supervisor_module
from harness_server.config import RuntimeConfig
from harness_server.runtime import (
    STATE_SCHEMA_VERSION,
    RuntimePaths,
    RuntimeState,
    RuntimeStateError,
    pid_is_alive,
    process_is_owned,
    read_state,
    write_state,
)
from harness_server.supervisor import ProcessOwnershipError, Supervisor


def _state(tmp_path: Path, *, start_token: str = "test:start") -> RuntimeState:
    paths = RuntimePaths.from_root(tmp_path / "product")
    return RuntimeState(
        schema_version=STATE_SCHEMA_VERSION,
        instance_id="instance-123",
        pid=424242,
        process_start_token=start_token,
        host="127.0.0.1",
        port=18200,
        version="3.0.0b1",
        started_at="2026-07-28T00:00:00+00:00",
        log_path=str(paths.log_file),
        db_path=str(tmp_path / "runtime.db"),
    )


def test_pid_reuse_fails_ownership_even_when_command_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state(tmp_path, start_token="linux:old-start")
    monkeypatch.setattr(runtime_module, "pid_is_alive", lambda pid: True)
    monkeypatch.setattr(
        runtime_module,
        "process_start_token",
        lambda pid: "linux:new-start",
    )
    monkeypatch.setattr(
        runtime_module,
        "process_arguments",
        lambda pid: (
            "/usr/bin/python",
            "-m",
            "harness_server.runtime",
            "child",
            "--instance-id",
            state.instance_id,
        ),
    )

    assert process_is_owned(state) is False


def test_linux_zombie_is_not_classified_as_alive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A reaped-pending zombie is exited, not a foreign live process."""
    monkeypatch.setattr(runtime_module, "_linux_process_state", lambda pid: "Z")
    monkeypatch.setattr(
        runtime_module.os,
        "kill",
        lambda pid, sent_signal: pytest.fail("zombie check must not signal the PID"),
    )

    assert pid_is_alive(424242) is False


def test_substring_markers_do_not_establish_ownership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state(tmp_path)
    monkeypatch.setattr(runtime_module, "pid_is_alive", lambda pid: True)
    monkeypatch.setattr(
        runtime_module,
        "process_start_token",
        lambda pid: state.process_start_token,
    )
    monkeypatch.setattr(
        runtime_module,
        "process_arguments",
        lambda pid: (
            "/bin/sh",
            "-c",
            f"echo harness_server.runtime child {state.instance_id}",
        ),
    )

    assert process_is_owned(state) is False


def test_sigkill_is_refused_when_identity_changes_after_sigterm(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state(tmp_path)
    ownership_checks = iter((True, False))
    sent_signals: list[int] = []

    monkeypatch.setattr(
        supervisor_module,
        "process_is_owned",
        lambda candidate: next(ownership_checks),
    )
    monkeypatch.setattr(
        supervisor_module.os,
        "kill",
        lambda pid, sent_signal: sent_signals.append(sent_signal),
    )
    supervisor = Supervisor(RuntimePaths.from_root(tmp_path / "product"))
    monkeypatch.setattr(supervisor, "_wait_for_exit", lambda pid, timeout: False)

    with pytest.raises(ProcessOwnershipError, match="refusing force kill"):
        supervisor._terminate_owned(state, timeout=0)

    assert sent_signals == [signal.SIGTERM]
    assert signal.SIGKILL not in sent_signals


def test_failed_cleanup_retains_state_when_identity_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = RuntimePaths.from_root(tmp_path / "product")
    state = _state(tmp_path)
    write_state(paths, state)
    monkeypatch.setattr(supervisor_module, "pid_is_alive", lambda pid: True)
    monkeypatch.setattr(supervisor_module, "process_is_owned", lambda candidate: False)

    with pytest.raises(ProcessOwnershipError, match="retaining state"):
        Supervisor(paths)._cleanup_failed_start(state)

    assert read_state(paths) == state


def test_corrupt_state_is_reported_and_blocks_start(tmp_path: Path) -> None:
    paths = RuntimePaths.from_root(tmp_path / "product")
    paths.ensure()
    paths.state_file.write_text("{not-json", encoding="utf-8")
    paths.state_file.chmod(0o600)
    supervisor = Supervisor(paths)

    status = supervisor.status()
    assert status.state == "corrupt"
    assert status.running is False

    config = RuntimeConfig(
        port=18201,
        db_path=str(tmp_path / "runtime.db"),
        memories_dir=str(tmp_path / "memories"),
    )
    with pytest.raises(RuntimeStateError, match="unreadable"):
        supervisor.start(config, timeout=0.1)

    assert paths.state_file.read_text(encoding="utf-8") == "{not-json"
