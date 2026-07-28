"""learner.py 单元测试。"""

from deepseek_harness.learner import on_session_end


def test_session_end():
    """session 结束后应返回记录。"""
    result = on_session_end(session_id="test-001")
    assert result is not None


def test_session_end_no_args():
    """无参数时不应抛异常。"""
    result = on_session_end()
    assert result is not None
