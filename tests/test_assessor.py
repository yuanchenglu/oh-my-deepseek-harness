"""assessor.py 单元测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugins', 'digital-twin'))
from assessor import on_post_tool_call


def test_write_ok():
    """write 正常结果应返回 quality=ok"""
    r = on_post_tool_call(tool_name='write', result='file saved')
    assert r and r['quality'] == 'ok'


def test_write_empty():
    """write 空结果应返回 quality=warning"""
    r = on_post_tool_call(tool_name='write', result='')
    assert r and r['quality'] == 'warning'


def test_unknown_tool():
    """未知工具应返回 None"""
    r = on_post_tool_call(tool_name='search', result='data')
    assert r is None
