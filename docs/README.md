# Documentation Index

本目录是 `oh-my-deepseek-harness` 在 `develop` 分支上的产品、架构、质量和发布基线。

## 1. Review

- [`reviews/CODE_REVIEW_2026-07-27.md`](reviews/CODE_REVIEW_2026-07-27.md)  
  完整仓库 Code Review，包含 P0/P1/P2、证据、影响、修复原则和 Release Gate。

## 2. Architecture

- [`architecture/PRODUCT_ARCHITECTURE.md`](architecture/PRODUCT_ARCHITECTURE.md)  
  产品定位、用户、边界、能力域、用户旅程、产品原则和版本策略。

- [`architecture/TECHNICAL_ARCHITECTURE.md`](architecture/TECHNICAL_ARCHITECTURE.md)  
  当前架构、目标架构、Context Integrity、Session State、Server、Tool Contract、数据和安全设计。

## 3. Product

- [`product/PRD.md`](product/PRD.md)  
  Open-source Beta 完整 PRD：目标、非目标、12 个 Epic、功能/非功能需求、配置、状态机、验收和发布门槛。

## 4. Testing

- [`testing/TEST_PLAN.md`](testing/TEST_PLAN.md)  
  测试分层、环境隔离、完整用例矩阵、CI 和退出标准。

- [`testing/TEST_REPORT_2026-07-27.md`](testing/TEST_REPORT_2026-07-27.md)  
  本次 GitHub Actions 实际执行结果和 Release 判断。

### Executable regression specifications

- [`../tests/test_context_integrity_regressions.py`](../tests/test_context_integrity_regressions.py)
- [`../tests/test_release_readiness_regressions.py`](../tests/test_release_readiness_regressions.py)

已确认但未修复的缺陷采用 `strict xfail`，修复后必须移除 xfail 并转为永久回归测试。

## 5. Roadmap

- [`roadmap/OPEN_SOURCE_RELEASE_PLAN.md`](roadmap/OPEN_SOURCE_RELEASE_PLAN.md)  
  只围绕 Runtime Integrity、Data Integrity、Open-source Usability 和 Beta 验证，不新增功能。

## 6. 阅读顺序

### 产品/决策者

1. Product Architecture
2. PRD
3. Code Review
4. Open-source Release Plan

### 研发

1. Code Review
2. Technical Architecture
3. PRD
4. Test Plan
5. Test Report

### 外部贡献者

1. Code Review 的目标问题
2. Test Plan 对应用例
3. Technical Architecture 的目标边界
4. PRD 的 Definition of Done

## 7. 当前分支策略

后续默认在 `develop` 操作。`master` 只接收通过 Release Gate 的变更。
