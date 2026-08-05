"""Harness Server App Factory and domain endpoint tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from harness_server.config import RuntimeConfig
from harness_server.server import create_app


@pytest.fixture(scope="module")
def client(tmp_path_factory: pytest.TempPathFactory):
    root = tmp_path_factory.mktemp("harness-server")
    config = RuntimeConfig(
        db_path=str(root / "harness.db"),
        import_memories=False,
        memories_dir=str(root / "memories"),
    )
    with TestClient(create_app(config)) as test_client:
        yield test_client


class TestRuntimeProbes:
    def test_health_is_liveness_only(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "harness-server"}

    def test_ready_checks_storage_without_exposing_path(self, client: TestClient):
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}
        assert "db_path" not in response.text

    def test_version_is_distinct(self, client: TestClient):
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "harness-server"
        assert data["version"] == "3.0.0b1"
        assert data["api_version"] == "1"


class TestPlanEndpoints:
    def test_plan_create(self, client: TestClient):
        response = client.post(
            "/plan/create",
            json={"task_description": "设计数据库 schema、实现 API、编写测试"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "plan_id" in data
        assert "steps" in data
        assert len(data["steps"]) >= 3

    def test_plan_create_empty_description(self, client: TestClient):
        response = client.post("/plan/create", json={"task_description": ""})
        assert response.status_code == 422

    def test_plan_status_not_found(self, client: TestClient):
        response = client.get("/plan/status/nonexistent-id")
        assert response.status_code == 404


class TestMemoryEndpoints:
    def test_memory_tag(self, client: TestClient):
        response = client.post("/memory/tag", json={"content": "用户偏好简体中文注释"})
        assert response.status_code == 200
        data = response.json()
        assert "layer" in data
        assert "tags" in data

    def test_memory_filter(self, client: TestClient):
        response = client.post("/memory/filter", json={"lambda": 0.5})
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "included_layers" in data

    def test_default_startup_does_not_import_memory_files(
        self,
        client: TestClient,
    ):
        response = client.post("/memory/query", json={"limit": 100})
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestCheckpointEndpoints:
    def test_checkpoint_create(self, client: TestClient):
        # 先创建合法 Plan（TC-CP-001：Checkpoint 需要合法 Plan 归属）
        plan_resp = client.post(
            "/plan/create",
            json={"task_description": "设计数据库 schema、实现 API、编写测试"},
        )
        assert plan_resp.status_code == 200
        plan_id = plan_resp.json()["plan_id"]

        response = client.post(
            "/checkpoint/create",
            json={
                "plan_id": plan_id,
                "plan_steps": [
                    {"step_id": "s1", "text": "步骤一", "status": "completed"},
                    {"step_id": "s2", "text": "步骤二", "status": "pending"},
                ],
                "completed_step_ids": ["s1"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "checkpoint" in data
        assert data["checkpoint"]["plan_id"] == plan_id

    def test_checkpoint_review_not_found(self, client: TestClient):
        response = client.post("/checkpoint/review/nonexistent-id", json={})
        assert response.status_code == 404

    def test_checkpoint_chain(self, client: TestClient):
        response = client.get("/checkpoint/chain/test-plan-001")
        assert response.status_code == 200
        data = response.json()
        assert "checkpoints" in data
        assert data["plan_id"] == "test-plan-001"
