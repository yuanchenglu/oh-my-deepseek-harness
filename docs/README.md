# Documentation Index

本目录是 `oh-my-deepseek-harness` 在 `develop` 分支上的产品、架构、质量和发布基线。

> 当前状态：Plan Ready 已通过；`REL-000` 已完成；M0 `REL-001` 正在统一版本语义；G0 尚未通过；M1、Public Beta 和 Stable 均未开始。

## 1. Review

- [`reviews/CODE_REVIEW_2026-07-27.md`](reviews/CODE_REVIEW_2026-07-27.md)：P0/P1/P2、证据和修复原则。

## 2. Architecture

- [`architecture/PRODUCT_ARCHITECTURE.md`](architecture/PRODUCT_ARCHITECTURE.md)：产品定位、能力域、用户旅程、版本与边界。
- [`architecture/TECHNICAL_ARCHITECTURE.md`](architecture/TECHNICAL_ARCHITECTURE.md)：目标源码、Context、Session、Server、Tool、数据、安全与 Release 架构。

## 3. Product

- [`product/PRD.md`](product/PRD.md)：88 个 `FR-*`、固定外部契约、验收和 Release Gate。

## 4. Testing

- [`testing/TEST_PLAN.md`](testing/TEST_PLAN.md)：100 个唯一 Test ID、主责 Work ID、CI 通道和退出标准。
- [`testing/TEST_REPORT_2026-07-27.md`](testing/TEST_REPORT_2026-07-27.md)：历史基线 144 Passed / 12 strict XFAIL；不代表 Beta 可发布。
- [`testing/evidence/REL-000.md`](testing/evidence/REL-000.md)：规格发布契约同步证据。
- [`testing/evidence/REL-001.md`](testing/evidence/REL-001.md)：版本语义统一证据。

## 5. Decisions

- [`decisions/VERSIONING.md`](decisions/VERSIONING.md)：PEP 440、Plugin SemVer、Git Tag、Python 支持和 Stable 迁移规则。

## 6. Roadmap

- [`roadmap/OPEN_SOURCE_RELEASE_PLAN.md`](roadmap/OPEN_SOURCE_RELEASE_PLAN.md)：v2.2 主计划。
- [`roadmap/OPEN_SOURCE_RELEASE_PLAN_ERRATA_2.3.md`](roadmap/OPEN_SOURCE_RELEASE_PLAN_ERRATA_2.3.md)：RC/正式 Tag、REL-004、XFAIL ID、BETA-003 的规范性修正。

## 7. Traceability

- [`traceability/RELEASE_TRACEABILITY.md`](traceability/RELEASE_TRACEABILITY.md)：Work ID → Requirement/Test/Issue/PR/Commit/Evidence。

## 8. 阅读顺序

- 产品/决策者：Product Architecture → PRD → Code Review → Release Plan。
- 研发：Code Review → Technical Architecture → PRD → Test Plan → Evidence。
- 外部贡献者：目标 Issue → 对应 Test ID → Architecture 边界 → Definition of Done。

## 9. 分支策略

后续默认在 `develop` 操作。`master` 只接收通过 Release Gate 的可发布基线。
