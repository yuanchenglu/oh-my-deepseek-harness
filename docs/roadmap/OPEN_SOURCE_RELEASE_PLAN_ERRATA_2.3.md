# OPEN_SOURCE_RELEASE_PLAN 2.3 规范性修正

- 状态：`NORMATIVE_AMENDMENT`
- 适用基线：`docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md` v2.2，commit `1d1c0b8`
- 适用分支：`develop`
- 生效范围：本文件与 v2.2 冲突时，以本文件为准
- 后续处理：在 `REL-002` 中合并回主计划并删除本临时修正文档

## 1. 修正目的

本修正关闭计划审核发现的四个结构性歧义，不改变 48 个 Work ID、G0–G5 Gate、100 个 Test ID 或总体发布范围。修正完成后允许从 `REL-000` 开始 M0；G0 通过前仍禁止进入 M1。

## 2. 修正一：消除 G3、test-release 与正式 Tag 的循环依赖

### 2.1 原冲突

原计划同时要求：

1. G3 前完成全量 `test-release`；
2. `test-release` 从干净 Tag 构建；
3. 正式不可变 Beta Tag 在 G3 通过后才创建。

这会形成 `G3 → Tag → test-release → G3` 的循环。

### 2.2 规范性替代规则

发布候选验证固定分为两层：

1. **G3 RC 验证**：对冻结的精确 Commit SHA 构建，或使用可删除的临时 RC Tag（例如 `v3.0.0-beta.1-rc.1`）。RC Tag 不得创建 GitHub Release，不得上传 PyPI，不得作为公开安装入口。
2. **正式 Beta 发布验证**：G3 通过并合入 `master` 后，对 `master` 的精确 Commit 重新构建最终制品并运行 `test-release`。只有该次验证通过，`BETA-001` 才能创建不可变 `v3.0.0-beta.1` Tag 和 GitHub Release。

正式 Tag 必须满足：

- 指向最终验证的同一 Commit；
- 制品 SHA256、SBOM、provenance 和 Release Notes 均引用该 Commit；
- 不覆盖、不移动、不复用已有 Tag；
- 最终验证失败时不得创建正式 Tag 或半套 Release。

### 2.3 对原章节的覆盖

- G3 中“Release 制品生成成功”解释为 **RC 制品**，不要求正式不可变 Beta Tag 已存在。
- `test-release` 的“从干净 Tag 构建”在 G3 阶段允许替换为“从冻结 Commit SHA 或临时 RC Tag 构建”。
- 正式 `v3.0.0-beta.1` Tag 仅由 `BETA-001` 创建。

## 3. 修正二：限定 REL-004，不提前实现第 10 个 Tool

### 3.1 当前事实

审查基线运行时注册 9 个公共 Tool；Beta 目标为 10 个，新增目标为 `memory_store`。

### 3.2 REL-004 固定边界

`REL-004` 只负责：

- 冻结 10 个目标 Tool 的名称、领域归属和 Contract 分母；
- 建立单一目标清单或常量；
- 同步 PRD、测试计划、README 和追踪口径；
- 明确“当前 9、目标 10”的迁移状态。

`REL-004` 不得：

- 注册不可工作的 `memory_store`；
- 提前实现 Memory 持久化；
- 提前重构 Tool Handler、FastAPI Model 或 Storage；
- 提前关闭 `TC-CONTRACT-*` 或 Memory 相关 Gate。

第 10 个 Tool 的实现职责固定为：

- `CON-001`：从 Pydantic Model 生成 10 个 Tool Schema，并建立统一 Contract/Envelope；
- `MEM-001`：实现 `memory_store` 的领域逻辑、持久化和对应测试。

在 `CON-001 + MEM-001` 完成前，运行时仍为 9 个 Tool 不构成 G0 失败；G0 只要求目标 Contract 和迁移计划已冻结。

## 4. 修正三：统一两个 XFAIL 的规范 ID

历史测试报告中的 ID 保持不改，规范 ID 固定为：

| 规范 ID | pytest node | 主责 Work ID | 废弃别名 |
|---|---|---|---|
| `XF-DEPS-001` | `tests/test_release_readiness_regressions.py::test_runtime_dependencies_include_openai` | `PKG-002` | `XF-PKG-001` |
| `XF-RELEASE-001` | `tests/test_release_readiness_regressions.py::test_project_versions_are_consistent` | `REL-001` | `XF-VERSION-001` |

执行规则：

- 新建 Issue、追踪矩阵、证据文档和 PR 只使用规范 ID；
- 废弃别名仅用于定位 v2.2 原文，不得继续传播；
- `REL-003` 必须把 v2.2 中的两个别名替换为规范 ID；
- 历史测试报告不回写，以保持证据不可变。

## 5. 修正四：补齐 BETA-003 的前置依赖与完成条件

M5 强制依赖改为：

```text
G3 → BETA-001
BETA-001 → BETA-002
BETA-001 → BETA-003
BETA-001 → REL-007
BETA-002 + BETA-003 + REL-007 → G4
```

`BETA-003` 只有在以下条件全部满足时才可完成：

1. Beta 期间每个失败均记录环境、复现、严重度和根因分类；
2. 每个需要代码修改的失败均创建独立 Work ID/Issue；
3. P0 立即暂停推广并阻断 G4；
4. P1 已关闭或具备符合计划第 4 节的有效 Waiver；
5. 修复后重新执行所有受影响 Gate；
6. 需要重新发布时递增预发布号，不覆盖已有 Tag 或制品；
7. Failure Ledger 中不存在“未分类、无 Owner、无下一步”的开放记录。

## 6. 开工判定

本规范性修正合入 `develop` 后：

- Plan Ready Gate 维持 `PASS`；
- 允许创建并执行 `REL-000`；
- 不允许直接进入 `REL-001` 之后的任务，除非其硬依赖已按计划完成；
- G0 仍为未通过状态；
- 产品仍不满足 Public Beta 或 Stable 发布条件。

## 7. REL-002 合并要求

`REL-002` 必须将本文件内容合并回 `OPEN_SOURCE_RELEASE_PLAN.md`，至少更新：

- 文档版本与 Update Log；
- G3 与 `test-release` 的 RC/正式 Tag 语义；
- M5 依赖图；
- `REL-004` 工作边界和附录 A；
- §7 与 §7.1 的两个 XFAIL ID；
- 发布与回滚流程；
- 附录 Q#2、Q#3 的回答。

合并完成并验证无冲突后，删除本文件。