"""Single runtime environment contract for Harness Server."""

from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

ENV_HOST = "HARNESS_HOST"
ENV_PORT = "HARNESS_PORT"
ENV_DB_PATH = "HARNESS_DB_PATH"
ENV_IMPORT_MEMORIES = "HARNESS_IMPORT_MEMORIES"
ENV_MEMORIES_DIR = "HARNESS_MEMORIES_DIR"
RUNTIME_ENV_VARS = frozenset(
    {
        ENV_HOST,
        ENV_PORT,
        ENV_DB_PATH,
        ENV_IMPORT_MEMORIES,
        ENV_MEMORIES_DIR,
    }
)


def _parse_bool(value: str, *, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def _validate_loopback(host: str) -> str:
    normalized = host.strip()
    if normalized.lower() == "localhost":
        return "localhost"
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError as exc:
        raise ValueError(f"{ENV_HOST} must be a loopback address") from exc
    if not address.is_loopback:
        raise ValueError(f"{ENV_HOST} must be a loopback address")
    return normalized


@dataclass(frozen=True)
class RuntimeConfig:
    """Validated local-runtime settings.

    Remote binding is deliberately out of scope for the Public Beta baseline.
    """

    host: str = "127.0.0.1"
    port: int = 8200
    db_path: str = "~/.hermes/mcp/harness.db"
    import_memories: bool = False
    memories_dir: str = "~/.hermes/memories"

    def __post_init__(self) -> None:
        object.__setattr__(self, "host", _validate_loopback(self.host))
        if not 1 <= int(self.port) <= 65535:
            raise ValueError(f"{ENV_PORT} must be between 1 and 65535")
        object.__setattr__(self, "port", int(self.port))
        object.__setattr__(self, "db_path", str(Path(self.db_path).expanduser()))
        object.__setattr__(
            self,
            "memories_dir",
            str(Path(self.memories_dir).expanduser()),
        )

    @property
    def url_host(self) -> str:
        return f"[{self.host}]" if ":" in self.host else self.host

    @property
    def server_url(self) -> str:
        return f"http://{self.url_host}:{self.port}"

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "RuntimeConfig":
        env = os.environ if environ is None else environ
        port_text = env.get(ENV_PORT, "8200")
        try:
            port = int(port_text)
        except ValueError as exc:
            raise ValueError(f"{ENV_PORT} must be an integer") from exc
        return cls(
            host=env.get(ENV_HOST, "127.0.0.1"),
            port=port,
            db_path=env.get(ENV_DB_PATH, "~/.hermes/mcp/harness.db"),
            import_memories=_parse_bool(
                env.get(ENV_IMPORT_MEMORIES, "0"),
                name=ENV_IMPORT_MEMORIES,
            ),
            memories_dir=env.get(ENV_MEMORIES_DIR, "~/.hermes/memories"),
        )
