"""harness_server 合并服务端点测试。

用 FastAPI TestClient 测 3 组路由的核心端点，不依赖网络。
"""

import sys
from pathlib import Path

# 把 mcp 目录加到 path，让 import 能找到 harness_server
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp"))

from fastapi.testclient import TestClient

from harness_server.server import app

client = TestClient(app)


class TestHealth:
    def test_health_returns_ok(self):
        """健康检查应返回 ok。"""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestPlanEndpoints:
    """I-06 规划引擎端点。"""

    def test_plan_create(self):
        """创建 Plan 应返回 plan_id 和 steps。"""
        resp = client.post("/plan/create", json={"task_description": "设计数据库 schema、实现 API、编写测试"})
        assert resp.status_code == 200
        data = resp.json()
        assert "plan_id" in data
        assert "steps" in data
        assert len(data["steps"]) >= 3

    def test_plan_create_empty_description(self):
        """空任务描述应返回 422。"""
        resp = client.post("/plan/create", json={"task_description": ""})
        assert resp.status_code == 422

    def test_plan_status_not_found(self):
        """不存在的 plan_id 应返回 404。"""
        resp = client.get("/plan/status/nonexistent-id")
        assert resp.status_code == 404


class TestMemoryEndpoints:
    """I-12 记忆标签端点。"""

    def test_memory_tag(self):
        """标签分类应返回 layer 和 tags。"""
        resp = client.post("/memory/tag", json={"content": "用户偏好简体中文注释"})
        assert resp.status_code == 200
        data = resp.json()
        assert "layer" in data
        assert "tags" in data

    def test_memory_filter(self):
        """λ 过滤应返回 entries 列表。"""
        resp = client.post("/memory/filter", json={"lambda": 0.5})
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert "included_layers" in data


class TestCheckpointEndpoints:
    """I-11 快照审查端点。"""

    def test_checkpoint_create(self):
        """创建 Checkpoint 应返回 checkpoint 对象。"""
        resp = client.post("/checkpoint/create", json={
            "plan_id": "test-plan-001",
            "plan_steps": [
                {"step_id": "s1", "text": "步骤一", "status": "completed"},
                {"step_id": "s2", "text": "步骤二", "status": "pending"},
            ],
            "completed_step_ids": ["s1"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "checkpoint" in data
        assert data["checkpoint"]["plan_id"] == "test-plan-001"

    def test_checkpoint_review_not_found(self):
        """不存在的 checkpoint_id 应返回 404。"""
        resp = client.post("/checkpoint/review/nonexistent-id", json={})
        assert resp.status_code == 404

    def test_checkpoint_chain(self):
        """获取 Checkpoint 链应返回列表。"""
        resp = client.get("/checkpoint/chain/test-plan-001")
        assert resp.status_code == 200
        data = resp.json()
        assert "checkpoints" in data
        assert data["plan_id"] == "test-plan-001"
