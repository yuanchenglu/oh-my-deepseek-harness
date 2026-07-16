"""
工具调用质量评估器 — 平台无关核心。

评估单次工具调用的结果内容完整性和 I-01 约束违反检测。
不依赖任何 Hermes API，通过函数参数接收所有平台特定输入。

约束违反检测使用 gate.py 的 _current_hard_constraints 横切状态通道，
该通道在 build_gate_context() 中由用户消息提取更新。
"""

import datetime
import logging
import os
import re
from typing import Any, Dict, Optional

from .gate import _current_hard_constraints

logger = logging.getLogger(__name__)

# 常见中文约束关键词 → 英文路径/命令关键词映射
_COMMON_TRANSLATIONS: dict[str, set[str]] = {
    "配置": {"config", "conf", "cfg", "ini", "yaml", "yml", "toml", "json", "xml", "properties"},
    "设置": {"setting", "config", "pref", "option"},
    "删除": {"delete", "rm", "remove", "del", "clean", "purge", "wipe"},
    "数据库": {"database", "db", "mysql", "postgres", "postgresql", "mongo",
               "mongodb", "sqlite", "redis", "sql", "mariadb", "oracle"},
    "密码": {"password", "passwd", "secret", "token", "credential", "auth"},
    "密钥": {"secret", "key", "certificate", "pem", "p12", "jks"},
    "日志": {"log", "logging", "journal", "syslog"},
    "缓存": {"cache", "buffer", "tmp"},
    "临时": {"temp", "tmp", "temporary"},
    "备份": {"backup", "bak", "dump", "snapshot"},
    "环境": {"env", "environment", "venv", ".env"},
    "依赖": {"depend", "requirement", "package", "module"},
    "安装": {"install", "setup", "bootstrap", "brew", "apt", "pip", "npm"},
    "目录": {"dir", "directory", "folder", "path"},
    "文件": {"file", "fs", "filesystem"},
    "脚本": {"script", "sh", "bash", "zsh", "py"},
    "进程": {"process", "pid", "service", "daemon", "systemd"},
    "服务": {"service", "daemon", "server", "systemd"},
    "网络": {"network", "net", "internet", "proxy", "dns", "dhcp"},
    "端口": {"port", "listen", "bind"},
    "证书": {"cert", "certificate", "pem", "crt", "ca", "tls", "ssl"},
    "仓库": {"repo", "repository", "registry", "docker", "image"},
    "系统": {"system", "sys", "kernel", "os"},
}


# ── I-01 辅助函数：约束匹配与记录 ──


def extract_keywords(text: str) -> set[str]:
    """从约束文本中提取关键词用于路径/命令匹配检测。

    返回中文词组（>=2 字）和英文单词（>=3 字母）的混合集合，
    包含原文关键词及其英文翻译等价物。
    """
    keywords: set[str] = set()
    # 中文词组（>=2 字）
    for m in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        keywords.add(m)
        # 添加英文翻译等价物
        for cn, en_set in _COMMON_TRANSLATIONS.items():
            if cn in m:
                keywords.update(en_set)
    # 英文单词（>=3 字母）
    for m in re.findall(r"[a-zA-Z]{3,}", text.lower()):
        keywords.add(m)
    return keywords


def check_path_against_constraint(file_path: str, constraint: str) -> bool:
    """检查文件路径是否命中约束关键词。

    同时检查路径的完整字符串和分段组件（去扩展名后的文件名、父目录名）。
    """
    path_lower = file_path.lower()
    keywords = extract_keywords(constraint)
    # 检查完整路径是否包含任何关键词
    if any(kw in path_lower for kw in keywords):
        return True
    # 检查文件名（去扩展名）是否包含任何关键词
    filename = os.path.basename(path_lower)
    name_no_ext = filename.rsplit(".", 1)[0] if "." in filename else filename
    if any(kw in name_no_ext for kw in keywords):
        return True
    # 检查父目录名
    parent = os.path.basename(os.path.dirname(path_lower))
    if any(kw in parent for kw in keywords):
        return True
    return False


def check_command_against_constraint(command: str, constraint: str) -> bool:
    """检查命令是否命中约束关键词。"""
    cmd_lower = command.lower()
    keywords = extract_keywords(constraint)
    return any(kw in cmd_lower for kw in keywords)


DEFAULT_VIOLATIONS_FILE = os.path.expanduser("~/.hermes/memories/constraint-violations.md")


def record_violation(
    violation: Dict[str, Any],
    session_id: str,
    violations_file: str = DEFAULT_VIOLATIONS_FILE,
) -> None:
    """将违反记录追加到 violations_file，异常时静默降级。

    Args:
        violation: 违反记录 dict（含 constraint, tool, evidence）
        session_id: 当前会话 ID
        violations_file: 违反记录持久化文件路径
    """
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = (
            f"\n## {now}\n"
            f"- **约束**: {violation['constraint']}\n"
            f"- **工具**: {violation['tool']}\n"
            f"- **证据**: {violation['evidence']}\n"
            f"- **会话**: {session_id}\n"
        )
        parent_dir = os.path.dirname(violations_file)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        with open(violations_file, "a", encoding="utf-8") as f:
            f.write(entry)
        logger.info(
            "约束违反记录已写入: %s — %s",
            violation["constraint"],
            violation["tool"],
        )
    except PermissionError:
        logger.warning("写入约束违反记录文件权限不足: %s", violations_file)
    except OSError as e:
        logger.warning(
            "写入约束违反记录文件 IO 错误: %s — %s", violations_file, e
        )


def check_constraint_violation(
    tool_name: str,
    args: dict,
    session_id: str,
    violations_file: str = DEFAULT_VIOLATIONS_FILE,
) -> Optional[Dict[str, Any]]:
    """检查工具调用是否违反活跃硬约束。

    对写类工具检查文件路径，对执行类工具检查命令文本。
    无活跃约束或工具类型不匹配时返回 None。

    Args:
        tool_name: 工具名称
        args: 工具调用参数
        session_id: 当前会话 ID
        violations_file: 违反记录文件路径

    Returns:
        dict: {"quality": "violation", "constraint": str, "evidence": str, "tool": str}
        无违反时返回 None。
    """
    if not _current_hard_constraints:
        return None

    for constraint in list(_current_hard_constraints):
        if tool_name in ("write", "edit", "apply_patch"):
            file_path = args.get("filePath", args.get("path", ""))
            if isinstance(file_path, str) and check_path_against_constraint(
                file_path, constraint
            ):
                violation = {
                    "quality": "violation",
                    "constraint": constraint,
                    "evidence": f"{tool_name} 调用了 {file_path}",
                    "tool": tool_name,
                }
                record_violation(violation, session_id, violations_file)
                return violation

        if tool_name in ("bash", "curl"):
            command = args.get("command", "")
            if isinstance(command, str) and check_command_against_constraint(
                command, constraint
            ):
                violation = {
                    "quality": "violation",
                    "constraint": constraint,
                    "evidence": f"{tool_name} 执行了: {command[:200]}",
                    "tool": tool_name,
                }
                record_violation(violation, session_id, violations_file)
                return violation

    return None


# ── 主入口 ──


def assess_tool_call(
    tool_name: str,
    args: dict,
    result: Any,
    session_id: str = "unknown",
    violations_file: str = DEFAULT_VIOLATIONS_FILE,
) -> Optional[Dict[str, Any]]:
    """评估单次工具调用的结果内容完整性。

    两步检查：
      1. I-01 约束违反检测（优先返回，对所有工具类型生效）
      2. 内容完整性检查（write/read/bash/browser 等）

    Args:
        tool_name: 工具名称
        args: 工具调用的参数
        result: 工具返回的文本结果
        session_id: 当前会话 ID
        violations_file: 约束违反记录文件路径

    Returns:
        None: 跳过评估（工具类型不在检查范围内）。
        Dict: {"quality": "ok" | "warning" | "violation", "tool": str, ...}
    """
    # ── I-01: 约束违反检测（对所有工具类型生效） ──
    violation = check_constraint_violation(tool_name, args, session_id, violations_file)
    if violation:
        return violation

    # ── 内容完整性检查 ──
    result_str: str = str(result) if result is not None else ""

    # ── 文件写入类工具：write / edit ──
    if tool_name in ("write", "edit", "apply_patch"):
        if result_str.strip():
            return {
                "quality": "ok",
                "tool": tool_name,
                "note": "结果非空，写入/编辑操作已完成",
            }
        else:
            return {
                "quality": "warning",
                "tool": tool_name,
                "note": "结果为空，write/edit 可能未写入内容或执行失败",
            }

    # ── 文件读取类工具：read ──
    if tool_name == "read":
        lines: list[str] = [line for line in result_str.split("\n") if line.strip()]
        if len(lines) > 0:
            return {
                "quality": "ok",
                "tool": tool_name,
                "note": f"读取到 {len(lines)} 行有效内容",
            }
        else:
            return {
                "quality": "warning",
                "tool": tool_name,
                "note": "读取结果行为空，文件可能不存在或内容为空",
            }

    # ── 命令执行类工具：bash / curl / webfetch ──
    if tool_name in ("bash", "curl", "webfetch", "websearch"):
        if result_str.strip():
            return {
                "quality": "ok",
                "tool": tool_name,
                "note": "执行结果非空，命令已正常输出",
            }
        else:
            return {
                "quality": "warning",
                "tool": tool_name,
                "note": "执行结果为空，命令可能未产生输出或执行失败",
            }

    # ── 浏览器/截图类工具 ──
    if tool_name in (
        "browser",
        "chrome",
        "screenshot",
        "take_screenshot",
        "look_at",
    ):
        if "base64" in result_str or "png" in result_str or "image" in result_str.lower():
            return {
                "quality": "ok",
                "tool": tool_name,
                "note": "结果包含图片数据，截图/浏览器操作已完成",
            }
        else:
            return {
                "quality": "warning",
                "tool": tool_name,
                "note": "结果未包含图片数据，截图/浏览器操作可能未正确执行",
            }

    # ── MCP / 其他工具：不评估，跳过 ──
    return None
