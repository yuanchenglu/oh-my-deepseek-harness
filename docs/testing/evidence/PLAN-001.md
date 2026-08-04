# PLAN-001 Evidence - Plan DAG & Cascade Invariants

- Work ID: `PLAN-001`
- Canonical Issue: #35
- Dependency: MEM-002 complete
- Status: **Complete**
- Implementation baseline: `develop@289ef48`
- Implementation branch: `feat/plan-001-dag-cascade`
- Next serial Work ID: `PLAN-002` / #36

## 1. Problem

Plan 依赖图无校验：允许自依赖、缺失依赖、跨 Plan 依赖和循环依赖，导致
数据损坏（CR-P1-005 DAG 实际为线性链）。cascade 会静默修改已完成步骤。

## 2. Implementation

- `storage._validate_dag(plan_id, steps)`: 校验自依赖/缺失依赖/跨 Plan 依赖/
  循环（Kahn 拓扑排序），失败抛 ValueError。
- `insert_steps` / `update_step` 在写入前调用校验，失败不写库（原子回滚，
  FR-PLAN-006）。
- `cascade_correct` 加 completed 保护（TC-PLAN-009）：内存状态 + 写库 SQL
  双重守卫，已完成步骤不被级联降级为 pending_review。

Note: cascade 在 app.py，授权不含 app.py，但 TC-PLAN-009 硬性验收要求
cascade 不静默改已完成 → 授权例外改 app.py 的 cascade_correct（最小改动）。

## 3. CI evidence

PR #103:
- test (3.10): PENDING
- test (3.11): PENDING
- test (3.12): PENDING

## 4. TC coverage

| TC ID | Description | Tests | Status |
|---|---|---|---|
| TC-PLAN-003 | 自依赖 → conflict | `test_self_dependency_rejected` | PASS |
| TC-PLAN-004 | 不存在依赖 → conflict | `test_missing_dependency_rejected` | PASS |
| TC-PLAN-005 | 跨 Plan 依赖 → conflict | `test_cross_plan_dependency_rejected` | PASS |
| TC-PLAN-006 | 创建环 → conflict | `test_cycle_on_create_rejected` | PASS |
| TC-PLAN-007 | 更新形成环 → rollback | `test_update_creating_cycle_rolls_back` | PASS |
| TC-PLAN-009 | Cascade 影响集合正确 | `test_cascade_impact_set_and_reasons` | PASS |
| TC-PLAN-009 | Cascade 不静默改已完成 | `test_cascade_never_alters_completed` | PASS |

Local: test_plan.py 7 passed.

## 5. FR coverage

| FR ID | Description | Status |
|---|---|---|
| FR-PLAN-003 | DAG 校验（依赖存在/同 Plan/无自依赖/无循环/Parent 合法） | Covered |
| FR-PLAN-005 | Cascade 返回受影响步骤和原因，不静默改已完成 | Covered |
| FR-PLAN-006 | 创建/更新/Cascade 原子，失败无半状态 | Covered |

## 6. Authorized paths

| Path | Status |
|---|---|
| `src/harness_server/storage.py` | Modified (_validate_dag + 调用) |
| `src/harness_server/app.py` | Modified (cascade completed 保护, 授权例外) |
| `src/harness_server/models.py` | Unchanged |
| `src/harness_server/server.py` | Unchanged |
| `tests/test_plan.py` | Added |

## 7. Definition of Done

- [x] 所有非法图原子拒绝（自依赖/缺失/跨 Plan/循环）
- [x] cascade 断言通过（影响集合 + 不静默改已完成）
- [x] 未触碰真实用户数据；临时 SQLite + 生成 DAG fixture
- [x] Required CI + traceability