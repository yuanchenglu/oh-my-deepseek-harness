"""MCP 自动发现测试（Spike 验证用）。

验证最小 MCP Server 可通过 stdio 传输模式启动和停止。
使用 Python 标准库 subprocess 模拟 MCP 协议交互。
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


def test_mcp_echo_server():
    """验证一个最小 MCP Echo Server 可以通过 stdio 启动和交互。

    使用 JSON-RPC 2.0 协议通过 stdin/stdout 与 MCP Server 通信。
    """
    # 找到可用的 Python
    python = _find_python()
    if not python:
        print("[SKIP] No suitable Python found")
        return

    # 创建一个最小的 MCP Echo Server 脚本
    echo_server_code = r'''
import json
import sys

def main():
    """Minimal MCP echo server (JSON-RPC over stdio)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": False
                        }
                    },
                    "serverInfo": {
                        "name": "echo-server",
                        "version": "0.1.0"
                    }
                }
            }
        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {
                            "name": "echo",
                            "description": "Echo back the input message",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"}
                                },
                                "required": ["message"]
                            }
                        }
                    ]
                }
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            if tool_name == "echo":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Echo: {args.get('message', '')}"
                            }
                        ]
                    }
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                }
        elif method == "notifications/initialized":
            # No response needed for notifications
            continue
        else:
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
'''

    # Write echo server to temp file
    import tempfile
    server_file = Path(tempfile.mktemp(suffix=".py"))
    try:
        server_file.write_text(echo_server_code)

        # Start server process
        proc = subprocess.Popen(
            [python, str(server_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        def _send_request(method: str, params: Optional[Dict] = None, req_id: int = 1) -> Dict:
            """Send JSON-RPC request and wait for response."""
            request = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
            }
            if params:
                request["params"] = params
            proc.stdin.write(json.dumps(request) + "\n")
            proc.stdin.flush()
            line = proc.stdout.readline()
            return json.loads(line.strip())

        try:
            # Test 1: Initialize
            print("  Sending initialize...")
            init_resp = _send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "0.1.0"},
            }, req_id=1)
            server_name = init_resp["result"]["serverInfo"]["name"]
            assert server_name == "echo-server"
            print(f"  [OK] Initialize: server={server_name}")

            # Send initialized notification (no response expected)
            proc.stdin.write(json.dumps({
                "jsonrpc": "2.0", "method": "notifications/initialized"
            }) + "\n")
            proc.stdin.flush()

            # Test 2: List tools
            print("  Listing tools...")
            tools_resp = _send_request("tools/list", req_id=2)
            tools = tools_resp["result"]["tools"]
            tool_names = [t["name"] for t in tools]
            assert "echo" in tool_names
            print(f"  [OK] tools/list: {tool_names}")

            # Test 3: Call echo tool
            print("  Calling echo tool...")
            call_resp = _send_request("tools/call", {
                "name": "echo",
                "arguments": {"message": "Hello MCP!"},
            }, req_id=3)
            echo_text = call_resp["result"]["content"][0]["text"]
            assert "Hello MCP!" in echo_text
            print(f"  [OK] tools/call echo: {echo_text}")

            print(f"\n  === MCP Echo Server: ALL TESTS PASSED ===")

        finally:
            # Clean shutdown
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
            print("  [OK] Server stopped")

    finally:
        if server_file.exists():
            server_file.unlink()


def _find_python() -> Optional[str]:
    """Find a suitable Python interpreter for running MCP server."""
    # Try common paths
    candidates = [
        "/opt/homebrew/bin/python3.13",
        "/opt/homebrew/bin/python3.12",
        "/opt/homebrew/bin/python3.11",
        "/usr/local/bin/python3",
        "/usr/bin/python3",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


if __name__ == "__main__":
    test_mcp_echo_server()
