# PLAN-003 Evidence - Plan Query & Lifecycle Controls

- Work ID: `PLAN-003`
- Canonical Issue: #37
- Dependency: PLAN-002 complete
- Status: **Complete**
- Implementation baseline: `develop@master`
- Implementation branch: `feat/plan-003-query-lifecycle`
- Next serial Work ID: `CP-001` / #38

## 1. Problem

Plan 查询/生命周期不完整：无归档能力、查询不含归档隔离、删除无确认保护。

## 2. Implementation

- `plans` 表加 `archived` 列（INTEGER DEFAULT 0）+ 旧库迁移（ALTER 补列）。
- `storage.archive_plan(plan_id)`: 归档 Plan（TC-PLAN-012）。
- `storage.delete_plan(plan_id)`: 删除 Plan 及步骤，只删目标（TC-PLAN-013）。
- `get_plan_meta(plan_id, include_archived=False)`: 默认排除归档，include 可查。
- `plan_status` 端点加 `include_archived` 查询参数，默认 404 归档 Plan。
- `cli plan archive/delete`: delete 缺 `--confirm` 返回 4 拒绝。
- 未新增公共 Tool（保持 10 个）。

## 3. CI evidence

PR #105:
- test (3.10): SUCCESS
- test (3.11): SUCCESS
- test (3.12): SUCCESS

## 4. TC coverage

| TC ID | Description | Tests | Status |
|---|---|---|---|
| TC-PLAN-011 | 按 ID 查询返回完整图或 not_found | `test_plan_status_returns_full_graph_or_not_found` | PASS |
| TC-PLAN-012 | Archive 后默认 Query 不返回，include 可返回 | `test_archive_excludes_from_default_query` | PASS |
| TC-PLAN-013 | 无确认拒绝；确认后只删目标 | `test_delete_requires_confirm_and_isolates_target` | PASS |

Local: test_plan.py 14 passed.

## 5. FR coverage

| FR ID | Description | Status |
|---|---|---|
| FR-PLAN-007 | plan_status/CLI 查看 Plan、依赖图、更新时间和异常状态 | Covered (TC-PLAN-011) |
| FR-PLAN-008 | Archive 默认排除 + 确认删除 | Covered (TC-PLAN-012/013) |

## 6. Authorized paths

| Path | Status |
|---|---|
| `src/harness_server/storage.py` | Modified (archived 列 + archive/delete) |
| `src/harness_server/app.py` | Modified (plan_status include_archived) |
| `src/deepseek_harness/cli.py` | Modified (plan archive/delete) |
| `src/harness_server/models.py` | Unchanged |
| `src/deepseek_harness/tools.py` | Unchanged |
| `tests/test_plan.py` | Modified (TC-PLAN-011/012/013) |

## 7. Definition of Done

- [x] Query/archive/confirmation/isolation 测试通过
- [x] 公共 Tool 数量保持 10（未新增）
- [x] 未触碰真实用户数据；临时 SQLite + 合成 Plan fixture
- [x] Required CI + traceability