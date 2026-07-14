"""MCP Server 端到端测试 — FastAPI TestClient。

每个测试类独立加载 server 模块并清理 sys.modules 中冲突的条目
（每个 MCP 子目录有自己的 models.py，避免互相污染）。
"""

import os
import sys
import tempfile
import importlib
from pathlib import Path

import pytest

TMPDIR = Path(tempfile.mkdtemp(prefix="mcp_test_"))
MCP_DIR = Path(__file__).resolve().parent.parent / "mcp"

os.environ["PLAN_ENGINE_DB_PATH"] = str(TMPDIR / "plan-engine.db")
os.environ["MEMORY_TAGGER_DB_PATH"] = str(TMPDIR / "memory-tagger.db")
os.environ["CHECKPOINT_DB_PATH"] = str(TMPDIR / "checkpoint-review.db")
(TMPDIR / "memories").mkdir(parents=True, exist_ok=True)

from fastapi.testclient import TestClient


def _load_server_module(subdir: str, name: str):
    """从子目录加载 server 模块，完全隔离导入命名空间。"""
    # 清除先前加载的相同模块名
    for key in list(sys.modules.keys()):
        # 清除 models, engine, tagger, storage 等共享模块名
        if key in ("models", "engine", "tagger", "storage"):
            del sys.modules[key]

    mod_path = MCP_DIR / subdir / "server.py"
    # 使用 spec_from_file_location + 子目录 sys.path
    subdir_path = str(MCP_DIR / subdir)
    old_path = list(sys.path)

    # 明确将该子目录放在 sys.path 最前面
    sys.path = [subdir_path] + [p for p in sys.path if p != subdir_path]

    spec = importlib.util.spec_from_file_location(name, str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)

    # 恢复 sys.path
    sys.path = old_path
    return mod


# ========================================================================
# Plan Engine
# ========================================================================


class TestPlanEngine:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.client = TestClient(_load_server_module("plan-engine", "plan_engine_server").app)

    def test_health(self):
        r = self.client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    def test_create_plan(self):
        r = self.client.post(
            "/plan/create",
            json={"task_description": "实现用户登录模块，包括注册、登录、密码重置三个功能"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "plan_id" in data
        assert len(data["steps"]) >= 3

    def test_create_plan_empty_description(self):
        r = self.client.post("/plan/create", json={"task_description": ""})
        assert r.status_code == 422

    def test_create_plan_blank_description(self):
        r = self.client.post("/plan/create", json={"task_description": "   "})
        assert r.status_code == 422

    def test_get_plan_status_not_found(self):
        r = self.client.get("/plan/status/nonexistent-plan")
        assert r.status_code == 404

    def test_get_plan_status_ok(self):
        cr = self.client.post(
            "/plan/create",
            json={"task_description": "步骤1。步骤2。步骤3。"},
        )
        plan_id = cr.json()["plan_id"]
        r = self.client.get(f"/plan/status/{plan_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["plan_id"] == plan_id
        assert len(data["steps"]) >= 3
        assert "adjacency_list" in data

    def test_update_step_not_found(self):
        r = self.client.put(
            "/plan/step/nonexistent-step",
            json={"status": "completed"},
        )
        assert r.status_code == 404

    def test_cascade_no_plan(self):
        r = self.client.post(
            "/plan/cascade",
            json={"plan_id": "nonexistent", "modified_step_id": "step-1"},
        )
        assert r.status_code == 404


# ========================================================================
# Memory Tagger
# ========================================================================


class TestMemoryTagger:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.client = TestClient(
            _load_server_module("memory-tagger", "memory_tagger_server").app
        )

    def test_health(self):
        r = self.client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    def test_tag_content(self):
        r = self.client.post(
            "/memory/tag",
            json={"content": "永远不要在生产环境执行 rm -rf"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "tags" in data
        assert "layer" in data
        assert "confidence" in data

    def test_tag_empty_content(self):
        r = self.client.post("/memory/tag", json={"content": ""})
        # Pydantic 验证 min_length=1 → 422
        assert r.status_code == 422

    def test_query_empty(self):
        r = self.client.post("/memory/query", json={})
        assert r.status_code == 200
        data = r.json()
        assert "entries" in data
        assert "total" in data

    def test_filter_default(self):
        r = self.client.post("/memory/filter", json={"lambda": 0.5})
        assert r.status_code == 200
        data = r.json()
        assert "entries" in data

    def test_lambda_for_convergent(self):
        r = self.client.get("/memory/lambda/convergent")
        assert r.status_code == 200
        data = r.json()
        assert data["task_type"] == "convergent"
        assert "suggested_lambda" in data

    def test_lambda_for_unknown_type(self):
        r = self.client.get("/memory/lambda/unknown-type")
        assert r.status_code == 200
        data = r.json()
        assert "suggested_lambda" in data


# ========================================================================
# Checkpoint Review
# ========================================================================


class TestCheckpointReview:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.client = TestClient(
            _load_server_module("checkpoint-review", "checkpoint_review_server").app
        )

    def test_health(self):
        r = self.client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    def test_create_checkpoint(self):
        r = self.client.post(
            "/checkpoint/create",
            json={
                "plan_id": "plan-test-1",
                "plan_steps": [
                    {"step_id": "s1", "text": "第一步", "status": "completed"},
                    {"step_id": "s2", "text": "第二步", "status": "in_progress"},
                ],
                "completed_step_ids": ["s1"],
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "checkpoint" in data
        cp = data["checkpoint"]
        assert cp["plan_id"] == "plan-test-1"
        assert cp["checkpoint_number"] == 1
        assert len(cp["completed_steps_summary"]) == 1

    def test_create_checkpoint_empty_plan_id(self):
        r = self.client.post(
            "/checkpoint/create",
            json={"plan_id": "", "plan_steps": [], "completed_step_ids": []},
        )
        assert r.status_code == 422

    def test_review_checkpoint_not_found(self):
        r = self.client.post("/checkpoint/review/nonexistent-cp", json={})
        assert r.status_code == 404

    def test_create_and_review_checkpoint(self):
        cr = self.client.post(
            "/checkpoint/create",
            json={
                "plan_id": "plan-test-2",
                "plan_steps": [
                    {"step_id": "s1", "text": "第一步", "status": "completed"},
                    {"step_id": "s2", "text": "第二步", "status": "in_progress"},
                    {"step_id": "s3", "text": "第三步", "status": "pending"},
                ],
                "completed_step_ids": ["s1"],
                "unexpected_findings": ["发现 API 文档与实际行为不一致"],
            },
        )
        cp_id = cr.json()["checkpoint"]["checkpoint_id"]
        r = self.client.post(f"/checkpoint/review/{cp_id}", json={})
        assert r.status_code == 200
        data = r.json()
        assert data["checkpoint_id"] == cp_id
        result = data["review_result"]
        assert "alignment" in result
        assert "progress_status" in result
        assert "confidence" in result

    def test_get_checkpoint_chain(self):
        self.client.post(
            "/checkpoint/create",
            json={
                "plan_id": "plan-chain-test",
                "plan_steps": [{"step_id": "s1", "text": "第一步", "status": "completed"}],
                "completed_step_ids": ["s1"],
            },
        )
        self.client.post(
            "/checkpoint/create",
            json={
                "plan_id": "plan-chain-test",
                "plan_steps": [{"step_id": "s1", "text": "第一步", "status": "completed"}],
                "completed_step_ids": ["s1"],
            },
        )
        r = self.client.get("/checkpoint/chain/plan-chain-test")
        assert r.status_code == 200
        data = r.json()
        assert data["plan_id"] == "plan-chain-test"
        assert len(data["checkpoints"]) >= 2
