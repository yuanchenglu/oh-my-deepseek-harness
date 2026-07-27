# Open-source Release Traceability

本文件在 M0 建立机器可检索的追踪入口。`REL-003` 将扩展到全部 48 个 Work ID 和真实 Issue/PR 链接。

| Work ID | Requirement / Contract | Test | Issue | PR | Commit | Evidence | Status |
|---|---|---|---|---|---|---|---|
| `REL-000` | 版本、Tool、CLI、路径、安全默认值、支持范围、RC/Tag 顺序 | 100 Test ID 规格唯一性与冲突搜索 | #3 | #4 | `e18db7e` | [`REL-000.md`](../testing/evidence/REL-000.md) | Complete |
| `REL-001` | Python/Plugin/Git 版本映射与 Python 支持范围 | `test_project_versions_are_consistent` + manifest SemVer | #5 | #6 | `a97dfe4` | [`REL-001.md`](../testing/evidence/REL-001.md) | Complete |
| `REL-002` | `develop` 集成、`master` 发布、PR 模板、Ruleset、默认分支和 v2.3 计划合并 | 文档冲突搜索 + repository metadata + administrator attestation + archive Blob identity | #7 | #8 + #9 | `e7e1414e` + `61642f69` | [`REL-002.md`](../testing/evidence/REL-002.md) | Complete |
| `REL-004` | 目标 10 Tool 名称、当前 9 Tool Runtime 与 pending 迁移状态 | `TestToolContract` + 9 Tool registration tests | #10 | #11 | `7d52de9f` | [`REL-004.md`](../testing/evidence/REL-004.md) | Complete |
| `GOV-001` | Security Policy、Issue Forms、PR 安全入口与 Release Checklist | Issue Form YAML parse + link/field checks + Required CI | #12 | 待创建 | 待合入 | [`GOV-001.md`](../testing/evidence/GOV-001.md) | In Progress |
