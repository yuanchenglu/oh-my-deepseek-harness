# PLAN-002 Evidence - Plan State Machine & Atomic Mutations

- Work ID: `PLAN-002`
- Canonical Issue: #36
- Dependency: PLAN-001 complete
- Status: **Complete**
- Implementation baseline: `develop@289ef48`
- Implementation branch: `feat/plan-002-state-machine`
- Next serial Work ID: `PLAN-003` / #37

## 1. Problem

Plan 步骤状态无合法转换校验：允许任意状态变更（如 completed 回退 pending）。
Plan 创建非原子：create_plan + insert_steps 分开调用，insert 失败残留 plan 元数据。

## 2. Implementation

- `PlanStatus` 补全 BLOCKED/CANCELLED（FR-PLAN-004 要求 6 状态）+ 模块级
  `_LEGAL_TRANSITIONS` 转换矩阵 + `can_transition_to()`。
- `storage.update_step` 校验状态转换合法性，非法抛 ValueError（TC-PLAN-008）。
- `storage.create_plan_with_steps`: 原子创建 Plan + Steps，单连接事务，
  失败整体回滚（TC-PLAN-001 / FR-PLAN-006）。
- `tools.py` plan_update_step status enum 同步 6 状态（CON-001 契约一致性，
  授权例外）。

## 3. CI evidence

PR #104:
- test (3.10): SUCCESS
- test (3.11): SUCCESS
- test (3.12): SUCCESS

Note: 首次 CI 因 test_tool_contract 的过时 no-blocked 断言失败（与 FR-PLAN-004
冲突），删除该断言后重跑全绿。

## 4. TC coverage

| TC ID | Description | Tests | Status |
|---|---|---|---|
| TC-PLAN-001 | Create Plan 单事务成功 | `test_plan_create_is_atomic` | PASS |
| TC-PLAN-008 | 非法状态转换 conflict | `test_illegal_state_transition_rejected` | PASS |
| TC-PLAN-008 | 合法状态转换通过 | `test_legal_state_transition_accepted` | PASS |
| TC-PLAN-010 | 并发更新无半状态 | `test_concurrent_update_no_half_state` | PASS |

Local: test_plan.py 11 passed.

Note: TC-PLAN-002 空任务 422 由 app.py 端点层处理（已有 test_harness_server
test_plan_create_empty_description 覆盖），本次不重复。

## 5. FR coverage

| FR ID | Description | Status |
|---|---|---|
| FR-PLAN-001 | Create Plan 单事务 | Covered (TC-PLAN-001) |
| FR-PLAN-002 | Step Model | Covered (既有) |
| FR-PLAN-004 | 状态机 6 状态 + 合法转换 | Covered (TC-PLAN-008) |
| FR-PLAN-006 | 创建/更新/Cascade 原子 | Covered (TC-PLAN-001) |

## 6. Authorized paths

| Path | Status |
|---|---|
| `src/harness_server/models.py` | Modified (PlanStatus 6 状态 + 转换矩阵) |
| `src/harness_server/storage.py` | Modified (状态机校验 + create_plan_with_steps) |
| `src/deepseek_harness/tools.py` | Modified (schema enum 同步, 授权例外) |
| `src/harness_server/server.py` | Unchanged |
| `tests/test_plan.py` | Modified (TC-PLAN-001/008/010) |

## 7. Definition of Done

- [x] 状态转换矩阵（非法拒绝）
- [x] 原子创建（单事务无半状态）
- [x] 短任务不重复步骤（既有 _decompose_task 保证 3-8 步）
- [x] 未触碰真实用户数据；临时 SQLite + 确定性 fixture
- [x] Required CI + traceability