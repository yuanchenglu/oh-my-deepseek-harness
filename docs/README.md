# Documentation Index

本目录是 `oh-my-deepseek-harness` 在 `develop` 分支上的产品、架构、质量和发布基线。

> 当前状态：Plan Ready 已通过；`REL-000`、`REL-001` 已完成；M0 `REL-002` 正在完成 v2.3 主计划合并；G0 尚未通过；M1、Public Beta 和 Stable 均未开始。

## 1. Review

- [`reviews/CODE_REVIEW_2026-07-27.md`](reviews/CODE_REVIEW_2026-07-27.md)：P0/P1/P2、证据和修复原则。

## 2. Architecture

- [`architecture/PRODUCT_ARCHITECTURE.md`](architecture/PRODUCT_ARCHITECTURE.md)：产品定位、能力域、用户旅程、版本与边界。
- [`architecture/TECHNICAL_ARCHITECTURE.md`](architecture/TECHNICAL_ARCHITECTURE.md)：目标源码、Context、Session、Server、Tool、数据、安全与 Release 架构。

## 3. Product

- [`product/PRD.md`](product/PRD.md)：88 个 `FR-*`、固定外部契约、验收和 Release Gate。
- [`capabilities/STATUS.md`](capabilities/STATUS.md)：能力状态分级定义（Stable/Beta/Experimental/Degraded/Removed）。
- [`capabilities/CAPABILITY_MATRIX.md`](capabilities/CAPABILITY_MATRIX.md)：能力分级矩阵与证据链接。

## 3b. Guides（全新用户入口）

- [`guides/README.md`](guides/README.md)：生命周期/隐私/排障指南索引。
- [`guides/INSTALL.md`](guides/INSTALL.md)：安装（预览、安装、验证、幂等）。
- [`guides/UPGRADE.md`](guides/UPGRADE.md)：升级（预览、备份、迁移、回滚）。
- [`guides/UNINSTALL.md`](guides/UNINSTALL.md)：卸载（普通卸载、确认清除）。
- [`guides/DOCTOR.md`](guides/DOCTOR.md)：只读诊断、退出码、JSON 输出。
- [`guides/PRIVACY.md`](guides/PRIVACY.md)：外发同意、数据最小化、本地 API。
- [`guides/TROUBLESHOOTING.md`](guides/TROUBLESHOOTING.md)：用户错误、日志、恢复。
- [`release/KNOWN_LIMITATIONS.md`](release/KNOWN_LIMITATIONS.md)：已知限制与边界。

## 4. Testing

- [`testing/TEST_PLAN.md`](testing/TEST_PLAN.md)：100 个唯一 Test ID、主责 Work ID、CI 通道和退出标准。
- [`testing/TEST_REPORT_2026-07-27.md`](testing/TEST_REPORT_2026-07-27.md)：历史基线 144 Passed / 12 strict XFAIL；不代表 Beta 可发布。
- [`testing/evidence/REL-000.md`](testing/evidence/REL-000.md)：规格发布契约同步证据。
- [`testing/evidence/REL-001.md`](testing/evidence/REL-001.md)：版本语义统一证据。
- [`testing/evidence/REL-002.md`](testing/evidence/REL-002.md)：分支治理、设置确认与计划合并证据。

## 5. Decisions

- [`decisions/VERSIONING.md`](decisions/VERSIONING.md)：PEP 440、Plugin SemVer、Git Tag、Python 支持和 Stable 迁移规则。

## 6. Contributing and Governance

- [`../CONTRIBUTING.md`](../CONTRIBUTING.md)：Work ID、测试隔离、提交和 PR 要求。
- [`contributing/BRANCH_POLICY.md`](contributing/BRANCH_POLICY.md)：`develop` 集成、`master` 发布、Ruleset 与验证清单。
- [`../.github/pull_request_template.md`](../.github/pull_request_template.md)：执行级 PR 证据模板。

## 7. Roadmap

- [`roadmap/OPEN_SOURCE_RELEASE_PLAN.md`](roadmap/OPEN_SOURCE_RELEASE_PLAN.md)：规范性 v2.3 主计划，包含 Errata 四项修正和当前执行状态。
- [`roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)：只读完整任务账本归档；未被 v2.3 修改的条款继续按引用生效。

## 8. Traceability

- [`traceability/RELEASE_TRACEABILITY.md`](traceability/RELEASE_TRACEABILITY.md)：Work ID → Requirement/Test/Issue/PR/Commit/Evidence。

## 9. 阅读顺序

- 产品/决策者：Product Architecture → PRD → Code Review → Release Plan。
- 研发：Code Review → Technical Architecture → PRD → Release Plan → 目标 Work ID 归档条目 → Test Plan → Evidence。
- 外部贡献者：目标 Issue → 对应 Test ID → Branch Policy → Architecture 边界 → Definition of Done。

## 10. 分支状态

`develop` 已机器确认成为默认分支。`develop` 与 `master` 的目标 Ruleset 已由仓库管理员确认设置；当前连接器无法枚举 Ruleset，因此证据明确区分机器验证与管理员人工验证。`REL-002` 只有在本次计划合并 PR 通过 CI 并合入后才完成；G0 仍需后续 M0 Work ID。
