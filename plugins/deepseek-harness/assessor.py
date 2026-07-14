"""
工具调用质量评估器 — 评估单次工具调用的结果内容完整性。

通过 Hermes Plugin 的 post_tool_call Hook 注册，在每次工具调用完成后被触发。
不阻断流程，仅记录评估结论供后续（如 learner.py）使用。
"""

from typing import Optional, Dict, Any


def on_post_tool_call(**kwargs) -> Optional[Dict[str, Any]]:
    """评估单次工具调用结果的内容完整性。

    根据工具类型检查 result 是否为空或格式异常，返回评估结论或 None（跳过）。

    Args:
        **kwargs: 包含以下字段的上下文（来自 model_tools.py 的 emit）：
            - tool_name (str): 工具名称，如 "write", "read", "bash"
            - args (dict): 工具调用的参数
            - result (str): 工具返回的文本结果
            - task_id (str): 当前任务 ID
            - session_id (str): 当前会话 ID
            - tool_call_id (str): 工具调用 ID
            - turn_id (str): 轮次 ID
            - duration_ms (int): 工具执行耗时（毫秒）

    Returns:
        None: 跳过评估（工具类型不在检查范围内）。
        Dict: {
            "quality": "ok" | "warning",
            "tool": str,
            "note": str
        }

    注意：
        - 只检查**当前调用**的结果内容完整性，不依赖历史状态
        - 不调用 LLM，不做跨调用分析
        - 不阻断工具执行流程
    """
    # 安全取出字段，避免 KeyError
    tool_name: str = kwargs.get("tool_name", "")
    result: Any = kwargs.get("result", None)

    # result 为 None 时安全跳过
    if result is None:
        return None

    # 确保 result 为字符串（有些工具可能返回 bytes 或其他类型）
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
        # 按行分割，过滤空行后统计有效行数
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
        # 检查 result 是否包含 base64 图片数据或图片文件路径标记
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
