"""learner.py 单元测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugins', 'deepseek-harness'))
from learner import on_session_end


def test_session_end():
    """session 结束后应返回记录"""
    r = on_session_end(session_id='test-001')
    assert r is not None


def test_session_end_no_args():
    """无参数时不应抛异常"""
    r = on_session_end()
    assert r is not None
