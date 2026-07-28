"""Installed ``deepseek-harness`` command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from harness_server.config import RuntimeConfig
from harness_server.runtime import RuntimePaths, RuntimeStateError
from harness_server.supervisor import (
    ProcessOwnershipError,
    StartError,
    Supervisor,
    SupervisorError,
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
        "pid",
        "host",
        "port",
        "version",
        "healthy",
        "ready",
        "log_path",
    )
    for key in order:
        value = payload.get(key)
        if value is not None:
            print(f"{key}: {value}", file=output)


def _supervisor(args: argparse.Namespace) -> Supervisor:
    paths = RuntimePaths.from_root(args.data_root)
    return Supervisor(paths)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "server":
        parser.error("unsupported command")

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

    parser.error("unsupported server command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
