"""subagent_watch.py 单元测试。"""

from deepseek_harness.subagent_watch import on_subagent_start, on_subagent_stop


def test_start_returns_task_id():
    """start 应返回 task_id。"""
    result = on_subagent_start(child_subagent_id="sub-001")
    assert result and result["task_id"] == "sub-001"


def test_stop_completed():
    """正常结束应返回 quality=ok。"""
    result = on_subagent_stop(child_session_id="sub-001", child_status="completed")
    assert result and result["quality"] == "ok"


def test_stop_no_id():
    """无参数时 start/stop 都返回 None。"""
    assert on_subagent_start() is None
    assert on_subagent_stop() is None
