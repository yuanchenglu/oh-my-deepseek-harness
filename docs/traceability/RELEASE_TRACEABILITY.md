# Open-source Release Traceability

本文件在 M0 建立机器可检索的追踪入口。`REL-003` 将扩展到全部 48 个 Work ID 和真实 Issue/PR 链接。

| Work ID | Requirement / Contract | Test | Issue | PR | Commit | Evidence | Status |
|---|---|---|---|---|---|---|---|
| `REL-000` | 版本、Tool、CLI、路径、安全默认值、支持范围、RC/Tag 顺序 | 100 Test ID 规格唯一性与冲突搜索 | #3 | #4 | `e18db7e` | [`REL-000.md`](../testing/evidence/REL-000.md) | Complete |
| `REL-001` | Python/Plugin/Git 版本映射与 Python 支持范围 | `test_project_versions_are_consistent` + manifest SemVer | #5 | #6 | `a97dfe4` | [`REL-001.md`](../testing/evidence/REL-001.md) | Complete |
| `REL-002` | `develop` 集成、`master` 发布、PR 模板、Ruleset 与默认分支 | 文档冲突搜索 + repository settings verification | #7 | 待创建 | 待合入 | [`REL-002.md`](../testing/evidence/REL-002.md) | Blocked: external settings |
