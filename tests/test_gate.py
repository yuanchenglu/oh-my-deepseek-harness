"""gate.py 单元测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugins', 'digital-twin'))
from gate import on_pre_llm_call


def test_first_turn_contains_map():
    """首轮应包含 MAP.md 内容和 L1/L2 提醒"""
    r = on_pre_llm_call(is_first_turn=True)
    assert r is not None
    assert 'L1' in r['context']
    assert 'L2' in r['context']
    assert 'MAP' in r['context']


def test_non_first_turn_no_map():
    """非首轮不应包含 MAP.md"""
    r = on_pre_llm_call(is_first_turn=False)
    assert r is not None
    assert 'L1' in r['context']
    assert 'MAP' not in r['context']
