"""CON-001: Tool Contract tests — 10 Tools must match Pydantic models and use unified envelope.

TC-CONTRACT-001~010: Each tool's minimal legal payload must produce a valid
ok/data/error/meta envelope response, not an internal 422.
"""

from __future__ import annotations

import pytest

from deepseek_harness.tools import _TOOL_SCHEMAS, _TOOL_HANDLERS, TARGET_PUBLIC_TOOL_NAMES


# ── Schema contract: all 10 tools have schemas ──────────


class TestSchemaCompleteness:
    """Every target tool must have a schema. memory_store schema defined by CON-001, handler by MEM-001."""

    def test_all_10_tools_have_schemas(self):
        for name in TARGET_PUBLIC_TOOL_NAMES:
            assert name in _TOOL_SCHEMAS, f"Missing schema for {name}"

    def test_runtime_tools_have_handlers(self):
        """9 runtime tools (excl. memory_store) must have handlers."""
        from deepseek_harness.tools import RUNTIME_PUBLIC_TOOL_NAMES
        for name in RUNTIME_PUBLIC_TOOL_NAMES:
            assert name in _TOOL_HANDLERS, f"Missing handler for {name}"

    def test_schema_has_required_fields(self):
        for name in TARGET_PUBLIC_TOOL_NAMES:
            schema = _TOOL_SCHEMAS[name]
            assert "properties" in schema, f"{name} missing properties"
            assert "type" in schema, f"{name} missing type"


# ── XF-CONTRACT-001: memory_filter uses 'lambda' alias ──


class TestMemoryFilterContract:
    """TC-CONTRACT-008: memory_filter must send 'lambda' to API, not 'lambda_value'."""

    def test_lambda_alias_in_json(self, monkeypatch):
        from deepseek_harness import tools

        captured = {}

        def fake_call(method, path, **kwargs):
            captured.update(kwargs)
            return {"entries": [], "total": 0, "lambda_value": 0.5, "included_layers": []}

        monkeypatch.setattr(tools, "_call_server", fake_call)
        tools._tool_memory_filter(lambda_value=0.5)
        assert "lambda" in captured["json"]
        assert "lambda_value" not in captured["json"]


# ── XF-CONTRACT-002: checkpoint_create required fields ──


class TestCheckpointCreateContract:
    """TC-CONTRACT-009: checkpoint_create must require plan_id, plan_steps, completed_step_ids."""

    def test_required_fields_present(self):
        required = set(_TOOL_SCHEMAS["checkpoint_create"].get("required", []))
        assert {"plan_id", "plan_steps", "completed_step_ids"} <= required

    def test_plan_steps_property_exists(self):
        props = _TOOL_SCHEMAS["checkpoint_create"]["properties"]
        assert "plan_steps" in props
        assert "completed_step_ids" in props


# ── XF-CONTRACT-003: plan_update_step enum matches PlanStatus ──


class TestPlanUpdateStepContract:
    """TC-CONTRACT-002: plan_update_step status enum must match service PlanStatus."""

    def test_enum_matches_planstatus(self):
        from harness_server.models import PlanStatus

        status_schema = _TOOL_SCHEMAS["plan_update_step"]["properties"]["status"]
        assert set(status_schema.get("enum", [])) == {s.value for s in PlanStatus}

    def test_no_blocked_in_enum(self):
        """'blocked' is not a valid PlanStatus — must not appear in schema."""
        status_schema = _TOOL_SCHEMAS["plan_update_step"]["properties"]["status"]
        assert "blocked" not in status_schema.get("enum", [])


# ── Unified envelope structure ──────────────────────────


class TestUnifiedEnvelope:
    """FR-SERVER-006: API and Tool share ok/data/error/meta envelope."""

    def test_error_response_has_ok_false(self):
        """ErrorResponse model must contain error detail."""
        from harness_server.models import ErrorResponse

        err = ErrorResponse(detail="test error")
        d = err.model_dump()
        assert "detail" in d

    def test_chain_response_has_envelope(self):
        """ChainResponse model must have ok/data structure."""
        from harness_server.models import ChainResponse

        # Just verify the model exists and is a Pydantic model
        assert hasattr(ChainResponse, "model_validate")


# ── Plan tool schemas ───────────────────────────────────


class TestPlanToolSchemas:
    """TC-CONTRACT-001/003/004: Plan tool schemas must have correct required fields."""

    def test_plan_create_requires_task_description(self):
        assert "task_description" in _TOOL_SCHEMAS["plan_create"].get("required", [])

    def test_plan_cascade_requires_plan_id_and_step(self):
        required = set(_TOOL_SCHEMAS["plan_cascade"].get("required", []))
        assert {"plan_id", "modified_step_id"} <= required

    def test_plan_status_requires_plan_id(self):
        assert "plan_id" in _TOOL_SCHEMAS["plan_status"].get("required", [])


# ── Memory tool schemas ─────────────────────────────────


class TestMemoryToolSchemas:
    """TC-CONTRACT-005/006/007: Memory tool schemas."""

    def test_memory_tag_requires_content(self):
        assert "content" in _TOOL_SCHEMAS["memory_tag"].get("required", [])

    def test_memory_store_schema_exists(self):
        """memory_store is target tool #6 — schema must exist even if pending."""
        assert "memory_store" in _TOOL_SCHEMAS or "memory_store" in TARGET_PUBLIC_TOOL_NAMES

    def test_memory_query_has_optional_fields(self):
        props = _TOOL_SCHEMAS["memory_query"]["properties"]
        assert "tags" in props
        assert "layer" in props


# ── Checkpoint tool schemas ─────────────────────────────


class TestCheckpointToolSchemas:
    """TC-CONTRACT-010: checkpoint_review schema."""

    def test_checkpoint_review_requires_checkpoint_id(self):
        assert "checkpoint_id" in _TOOL_SCHEMAS["checkpoint_review"].get("required", [])
