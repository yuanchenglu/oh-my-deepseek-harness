"""Installed ``deepseek-harness`` command-line interface."""

from __future__ import annotations

import argparse
import json
import sys

from harness_server.config import RuntimeConfig
from harness_server.runtime import RuntimePaths, RuntimeStateError
from harness_server.supervisor import (
    ProcessOwnershipError,
    StartError,
    Supervisor,
    SupervisorError,
)

from .doctor import (
    DOCTOR_MISSING_DEPENDENCY,
    DoctorCheck,
    DoctorReport,
    diagnose,
    render_human,
)
from .installer import InstallError, install
from .lifecycle import (
    LifecycleError,
    plan_from_environment,
    recover,
    uninstall,
    upgrade,
)


def _add_common_runtime_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--data-root",
        help="Product data root (default: ~/.hermes/oh-my-deepseek-harness)",
    )
    parser.add_argument("--json", action="store_true", help="Emit one JSON object")


def _add_start_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", help="Loopback host")
    parser.add_argument("--port", type=int, help="Local Server port")
    parser.add_argument("--db-path", help="SQLite database path")
    parser.add_argument("--memories-dir", help="Hermes Memory directory")
    parser.add_argument(
        "--import-memories",
        action="store_true",
        default=None,
        help="Import Hermes Memory files during startup",
    )
    parser.add_argument(
        "--no-import-memories",
        action="store_false",
        dest="import_memories",
        help="Disable startup Memory import",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deepseek-harness")
    commands = parser.add_subparsers(dest="command", required=True)

    install_command = commands.add_parser(
        "install", help="Deploy Hermes adapters and one local Harness Server"
    )
    _add_common_runtime_options(install_command)
    install_command.add_argument(
        "--dry-run", action="store_true", help="Report the transaction without writes"
    )
    install_command.add_argument("--timeout", type=float, default=20.0)

    doctor_command = commands.add_parser(
        "doctor", help="Run read-only environment and lifecycle diagnostics"
    )
    _add_common_runtime_options(doctor_command)

    upgrade_command = commands.add_parser(
        "upgrade", help="Back up and upgrade the managed deployment"
    )
    _add_common_runtime_options(upgrade_command)
    upgrade_command.add_argument(
        "--dry-run", action="store_true", help="Report backup and migration impact"
    )
    upgrade_command.add_argument("--timeout", type=float, default=20.0)

    recover_command = commands.add_parser(
        "recover", help="Restore an interrupted upgrade transaction"
    )
    _add_common_runtime_options(recover_command)
    recover_command.add_argument("--timeout", type=float, default=20.0)

    uninstall_command = commands.add_parser(
        "uninstall", help="Remove managed deployment while preserving distribution"
    )
    _add_common_runtime_options(uninstall_command)
    uninstall_command.add_argument(
        "--purge-data",
        action="store_true",
        help="Also delete the canonical product data root",
    )
    uninstall_command.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm destructive purge of canonical product data",
    )

    server = commands.add_parser("server", help="Manage the local Harness Server")
    actions = server.add_subparsers(dest="server_command", required=True)

    start = actions.add_parser("start", help="Start one managed local Server")
    _add_common_runtime_options(start)
    _add_start_options(start)
    start.add_argument("--timeout", type=float, default=20.0)

    status = actions.add_parser("status", help="Validate managed PID, port and probes")
    _add_common_runtime_options(status)

    stop = actions.add_parser("stop", help="Idempotently stop the managed Server")
    _add_common_runtime_options(stop)
    stop.add_argument("--timeout", type=float, default=10.0)

    restart = actions.add_parser("restart", help="Stop then start the managed Server")
    _add_common_runtime_options(restart)
    _add_start_options(restart)
    restart.add_argument("--stop-timeout", type=float, default=10.0)
    restart.add_argument("--start-timeout", type=float, default=20.0)

    memory = commands.add_parser("memory", help="Manage memory entries")
    memory_actions = memory.add_subparsers(dest="memory_command", required=True)
    _add_common_runtime_options(memory)

    memory_import = memory_actions.add_parser(
        "import", help="Import Hermes Memory .md files into the store"
    )
    memory_import.add_argument("--memories-dir", help="Hermes Memory directory")
    memory_import.add_argument(
        "--db-path", help="SQLite database path (default: RuntimeConfig.db_path)"
    )
    memory_import.add_argument(
        "--dry-run",
        action="store_true",
        help="Report per-file import impact without writing to the DB",
    )

    memory_delete = memory_actions.add_parser(
        "delete", help="Delete memory entries by source"
    )
    memory_delete.add_argument("--source", required=True, help="Memory source identity")
    memory_delete.add_argument(
        "--db-path", help="SQLite database path (default: RuntimeConfig.db_path)"
    )
    memory_delete.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm destructive deletion of memory entries",
    )

    plan = commands.add_parser("plan", help="Manage Plan lifecycle")
    plan_actions = plan.add_subparsers(dest="plan_command", required=True)
    _add_common_runtime_options(plan)

    plan_archive = plan_actions.add_parser(
        "archive", help="Archive a Plan (excluded from default queries)"
    )
    plan_archive.add_argument("--plan-id", required=True, help="Plan ID to archive")
    plan_archive.add_argument(
        "--db-path", help="SQLite database path (default: RuntimeConfig.db_path)"
    )

    plan_delete = plan_actions.add_parser(
        "delete", help="Delete a Plan and its steps"
    )
    plan_delete.add_argument("--plan-id", required=True, help="Plan ID to delete")
    plan_delete.add_argument(
        "--db-path", help="SQLite database path (default: RuntimeConfig.db_path)"
    )
    plan_delete.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm destructive deletion of the Plan",
    )
    return parser


def _runtime_config(args: argparse.Namespace) -> RuntimeConfig:
    base = RuntimeConfig.from_env()
    return RuntimeConfig(
        host=args.host if args.host is not None else base.host,
        port=args.port if args.port is not None else base.port,
        db_path=args.db_path if args.db_path is not None else base.db_path,
        import_memories=(
            args.import_memories
            if args.import_memories is not None
            else base.import_memories
        ),
        memories_dir=(
            args.memories_dir if args.memories_dir is not None else base.memories_dir
        ),
    )


def _emit(payload: dict, *, as_json: bool, stream=None) -> None:
    output = sys.stdout if stream is None else stream
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), file=output)
        return
    order = (
        "state",
        "message",
        "dry_run",
        "changed",
        "pid",
        "server_pid",
        "host",
        "port",
        "version",
        "current_version",
        "target_version",
        "healthy",
        "ready",
        "data_preserved",
        "distribution_preserved",
        "pip_uninstall_command",
        "backup_dir",
        "log_path",
    )
    rendered: set[str] = set()
    for key in order:
        value = payload.get(key)
        if value is not None:
            print(f"{key}: {_human_value(value)}", file=output)
            rendered.add(key)
    for key in sorted(set(payload) - rendered):
        print(f"{key}: {_human_value(payload[key])}", file=output)


def _human_value(value) -> str:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _supervisor(args: argparse.Namespace) -> Supervisor:
    paths = RuntimePaths.from_root(args.data_root)
    return Supervisor(paths)


def _run_install(args: argparse.Namespace) -> int:
    try:
        payload = install(
            dry_run=args.dry_run,
            timeout=args.timeout,
            data_root=args.data_root,
        )
        _emit(payload, as_json=args.json)
        return 0
    except ValueError as exc:
        _emit(
            {"state": "config_error", "message": str(exc)},
            as_json=args.json,
            stream=sys.stderr,
        )
        return 3
    except InstallError as exc:
        _emit(
            {"state": "install_error", "message": str(exc)},
            as_json=args.json,
            stream=sys.stderr,
        )
        return exc.exit_code


def _config_error_report(message: str) -> DoctorReport:
    return DoctorReport(
        (
            DoctorCheck(
                "config",
                "fail",
                "Runtime configuration is invalid",
                recovery="Correct the HARNESS_HOST, HARNESS_PORT and path settings, then rerun Doctor.",
                failure_class="missing_dependency",
                details={"error": message},
            ),
        ),
        DOCTOR_MISSING_DEPENDENCY,
    )


def _run_doctor(args: argparse.Namespace) -> int:
    try:
        report = diagnose(data_root=args.data_root)
    except ValueError as exc:
        report = _config_error_report(str(exc))
    if args.json:
        print(
            json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True),
            file=sys.stdout,
        )
    else:
        print(render_human(report), file=sys.stdout)
    return report.exit_code


def _run_lifecycle(args: argparse.Namespace) -> int:
    try:
        plan = plan_from_environment(data_root=args.data_root)
        if args.command == "upgrade":
            payload = upgrade(plan, dry_run=args.dry_run, timeout=args.timeout)
        elif args.command == "recover":
            payload = recover(plan, timeout=args.timeout)
        elif args.command == "uninstall":
            payload = uninstall(
                plan,
                purge_data=args.purge_data,
                confirm=args.confirm,
            )
        else:  # pragma: no cover - parser owns command set
            raise AssertionError("unsupported lifecycle command")
        _emit(payload, as_json=args.json)
        return 0
    except ValueError as exc:
        _emit(
            {"state": "config_error", "message": str(exc)},
            as_json=args.json,
            stream=sys.stderr,
        )
        return 3
    except (LifecycleError, ProcessOwnershipError, RuntimeStateError) as exc:
        exit_code = getattr(exc, "exit_code", 4)
        _emit(
            {"state": "lifecycle_error", "message": str(exc)},
            as_json=args.json,
            stream=sys.stderr,
        )
        return int(exit_code)


def _run_memory(args: argparse.Namespace) -> int:
    """处理 memory import / delete 子命令。

    - import: 将 Hermes Memory .md 文件导入存储；--dry-run 只报告不写库。
    - delete: 按 source 删除记忆；缺 --confirm 时拒绝（FR-MEMORY-006）。
    """
    try:
        from harness_server.storage import HarnessStorage

        db_path = args.db_path or RuntimeConfig.from_env().db_path
        store = HarnessStorage(db_path)

        if args.memory_command == "import":
            from harness_server.app import import_hermes_memories

            mem_dir = args.memories_dir or RuntimeConfig.from_env().memories_dir
            if args.dry_run:
                # dry-run：不写库，只统计影响（用临时 store 模拟）
                import tempfile

                with tempfile.TemporaryDirectory() as tmp:
                    dry_store = HarnessStorage(str(tmp) + "/dry.db")
                    imported, skipped, total = import_hermes_memories(mem_dir, dry_store)
                _emit(
                    {
                        "state": "dry_run",
                        "dry_run": True,
                        "imported": imported,
                        "skipped": skipped,
                        "total": total,
                        "db_path": db_path,
                    },
                    as_json=args.json,
                )
                return 0
            imported, skipped, total = import_hermes_memories(mem_dir, store)
            _emit(
                {
                    "state": "ok",
                    "imported": imported,
                    "skipped": skipped,
                    "total": total,
                    "db_path": db_path,
                },
                as_json=args.json,
            )
            return 0

        if args.memory_command == "delete":
            if not args.confirm:
                _emit(
                    {
                        "state": "confirm_required",
                        "message": "delete requires --confirm to proceed",
                        "source": args.source,
                    },
                    as_json=args.json,
                    stream=sys.stderr,
                )
                return 4
            deleted = store.delete_memories_by_source(args.source)
            _emit(
                {
                    "state": "ok",
                    "deleted": deleted,
                    "source": args.source,
                },
                as_json=args.json,
            )
            return 0

        raise AssertionError("unsupported memory command")
    except ValueError as exc:
        _emit(
            {"state": "config_error", "message": str(exc)},
            as_json=args.json,
            stream=sys.stderr,
        )
        return 3
    except RuntimeStateError as exc:
        _emit(
            {"state": "state_error", "message": str(exc)},
            as_json=args.json,
            stream=sys.stderr,
        )
        return 2


def _run_plan(args: argparse.Namespace) -> int:
    """处理 plan archive / delete 子命令。

    - archive: 归档 Plan（默认查询不返回，TC-PLAN-012）
    - delete: 删除 Plan；缺 --confirm 时拒绝（TC-PLAN-013）
    """
    try:
        from harness_server.storage import HarnessStorage

        db_path = args.db_path or RuntimeConfig.from_env().db_path
        store = HarnessStorage(db_path)

        if args.plan_command == "archive":
            ok = store.archive_plan(args.plan_id)
            _emit(
                {"state": "ok", "archived": ok, "plan_id": args.plan_id},
                as_json=args.json,
            )
            return 0 if ok else 4

        if args.plan_command == "delete":
            if not args.confirm:
                _emit(
                    {
                        "state": "confirm_required",
                        "message": "delete requires --confirm to proceed",
                        "plan_id": args.plan_id,
                    },
                    as_json=args.json,
                    stream=sys.stderr,
                )
                return 4
            ok = store.delete_plan(args.plan_id)
            _emit(
                {"state": "ok", "deleted": ok, "plan_id": args.plan_id},
                as_json=args.json,
            )
            return 0 if ok else 4

        raise AssertionError("unsupported plan command")
    except ValueError as exc:
        _emit(
            {"state": "config_error", "message": str(exc)},
            as_json=args.json,
            stream=sys.stderr,
        )
        return 3
    except RuntimeStateError as exc:
        _emit(
            {"state": "state_error", "message": str(exc)},
            as_json=args.json,
            stream=sys.stderr,
        )
        return 2


def _run_server(args: argparse.Namespace) -> int:
    supervisor = _supervisor(args)
    try:
        if args.server_command == "start":
            status = supervisor.start(_runtime_config(args), timeout=args.timeout)
            _emit(status.to_dict(), as_json=args.json)
            return 0
        if args.server_command == "status":
            status = supervisor.status()
            _emit(status.to_dict(), as_json=args.json)
            return 0 if status.running and status.healthy and status.ready else 1
        if args.server_command == "stop":
            status = supervisor.stop(timeout=args.timeout)
            _emit(status.to_dict(), as_json=args.json)
            return 0
        if args.server_command == "restart":
            status = supervisor.restart(
                _runtime_config(args),
                stop_timeout=args.stop_timeout,
                start_timeout=args.start_timeout,
            )
            _emit(status.to_dict(), as_json=args.json)
            return 0
    except ValueError as exc:
        _emit(
            {"state": "config_error", "message": str(exc)},
            as_json=args.json,
            stream=sys.stderr,
        )
        return 3
    except RuntimeStateError as exc:
        _emit(
            {"state": "state_error", "message": str(exc)},
            as_json=args.json,
            stream=sys.stderr,
        )
        return 2
    except StartError as exc:
        _emit(
            {
                "state": "start_error",
                "message": str(exc),
                "log_path": exc.log_path,
            },
            as_json=args.json,
            stream=sys.stderr,
        )
        return 2
    except (ProcessOwnershipError, SupervisorError) as exc:
        _emit(
            {"state": "runtime_error", "message": str(exc)},
            as_json=args.json,
            stream=sys.stderr,
        )
        return 2

    raise AssertionError("unsupported server command")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "install":
        return _run_install(args)
    if args.command == "doctor":
        return _run_doctor(args)
    if args.command in {"upgrade", "recover", "uninstall"}:
        return _run_lifecycle(args)
    if args.command == "server":
        return _run_server(args)
    if args.command == "memory":
        return _run_memory(args)
    if args.command == "plan":
        return _run_plan(args)
    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
