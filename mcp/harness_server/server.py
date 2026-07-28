"""Compatibility module forwarding to the installed harness_server implementation."""

from harness_server import server as _impl
from harness_server.server import *  # noqa: F401,F403


def __getattr__(name):
    return getattr(_impl, name)


if __name__ == "__main__":
    _impl.main()
