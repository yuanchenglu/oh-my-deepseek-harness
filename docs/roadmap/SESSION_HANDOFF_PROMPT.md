# 新会话交接提示词

```text
你继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格、串行、持续完成 Open-source Beta → Stable 全计划。除真实 Owner 外部门禁、外部平台审核或真实日历时间 Gate 外，不等待“继续”。每完成一个 Work ID 或 Gate，重新读取远程 develop 并启动下一个唯一合法任务。

一、远程唯一事实源

启动后核验 develop、master、全部远程分支、开放 PR、canonical Issues、Review Threads、CI、Artifacts、Tags、Releases 与 Rulesets，并完整阅读：

- docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md（v2.3.12 或更新）；
- docs/roadmap/EXECUTION_STATUS.md；
- docs/roadmap/SESSION_HANDOFF_PROMPT.md；
- docs/roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md；
- docs/testing/TEST_PLAN.md；
- docs/testing/evidence/GATE-G1.md；
- docs/testing/evidence/CTX-001.md；
- docs/testing/evidence/CTX-002.md；
- docs/testing/evidence/CTX-003.md；
- docs/testing/evidence/CTX-004.md；
- docs/traceability/RELEASE_TRACEABILITY.md；
- docs/product/PRD.md；
- docs/architecture/TECHNICAL_ARCHITECTURE.md；
- docs/compatibility/HERMES_MATRIX.md。

任何交接快照与 GitHub 事实冲突时，以远程事实为准并同步修正文档。

二、当前事实快照

- CTX-004 implementation baseline：develop@5ad013b3e121aa53eddce65a300e8ae737e14d21
- master：398701c5cf6495180a7a7566f09921cf126a054a
- develop 与 master 仍 diverged；不得强推或提前处理发布合并
- 固定 Work ID：48
- Complete：20/48（41.7%）
- Not started / dependency blocked：28/48
- M0：Complete
- G0：PASS
- M1：8/8 Complete
- G1：PASS
- CTX-001、CTX-002、CTX-003、CTX-004：Complete
- 产品成熟度：Experimental Preview
- 下一唯一合法任务：SES-001 / Issue #30
- master、Tag、GitHub Release、PyPI 均未进入发布阶段
- PyPI 按 REL-005 保持禁用

三、CTX-004 完成事实

- Issue #29：代码和证据闭环后应为 Closed / completed
- Governance Issue #88 / PR #89 / squash：dec84237c305fd8fa3e4dcf1b52002da5a8e7f7d
- Implementation PR #90：Merged
- Original P1 Red：Run #231 / ID 30462655418
- Stable-ID Red：Run #239 / ID 30465675428
- Failure-cooldown Red：Run #242 / ID 30466881933
- Final Head：e01c7fcc771460423628ebcf08b791cc927cb4c0
- Final CI：Run #243 / ID 30467133399
- Squash：5ad013b3e121aa53eddce65a300e8ae737e14d21
- Python 3.10/3.11/3.12：PASS
- Tests：251 passed / 6 strict XFAIL / 0 failed / 0 errors / 0 XPASS
- Wheel：42 files
- sdist：81 files
- Codex exact-final-Head review：+1
- PR #87 与 PR #90 unresolved Review Threads：0
- Evidence：docs/testing/evidence/CTX-004.md

四、当前唯一合法任务：SES-001 / Issue #30

不得并行启动 PRIV-001 或 G2。

启动步骤：

1. 读取最新 develop、Issue #30 与全部评论；
2. 核对 FR-POLICY-001–008、CR-P0-005、TC-POLICY-001–005、XF-POLICY-001；
3. 在 Issue #30 写启动评论，记录 baseline、scope、exclusions；
4. 从最新 develop 创建专用分支，例如 feat/ses-001-session-policy-store；
5. 先把 tests/test_release_readiness_regressions.py::test_hard_constraints_are_isolated_between_sessions 从 strict XFAIL 转成普通失败测试；
6. 增加 TC-POLICY-001–005，包括两线程 barrier、Session 隔离、显式 cancel、Session end cleanup 与无共享可变状态；
7. 推送 TDD commit，创建 Draft PR，记录 Red CI；
8. 仅实现最小正确的 canonical SessionPolicyStore；
9. Final Head 三版本 CI、Artifacts 与 Review 全部闭环后 expected-Head Squash Merge；
10. 创建 docs/testing/evidence/SES-001.md，更新 Plan/Status/Traceability/Handoff；
11. 关闭 #30 并自动进入 PRIV-001。

授权路径：

src/deepseek_harness/session_policy.py
src/deepseek_harness/gate.py
src/deepseek_harness/assessor.py
tests/test_gate_v2.py
tests/test_assessor_v2.py
tests/test_session_policy.py
tests/test_release_readiness_regressions.py
docs/testing/evidence/SES-001.md
owned trace/status/handoff rows

架构边界：

- Session Policy 的 canonical owner 必须唯一；
- Session ID 生命周期包含 start、switch、cancel、end、cleanup；
- 并发 Session 不得共享 mutable policy state；
- CTX-004 已有 per-Session compressor state，只属于 Context 模块内部指标/摘要状态；
- 不得建立第二份 Context state、第二套生产 Session Runtime 或第二个 Agent Loop；
- Durable Memory、Audit format、Tool contracts 与 Privacy 不属于 SES-001。

五、固定后续顺序

SES-001 → PRIV-001 → G2
G2 PASS → M3 → M4 → G3 → exact-master RC → v3.0.0-beta.1
Beta feedback → G4 → Stable preparation → SOAK-001（真实 14 天）→ G5 → v3.0.0

六、固定支持与发布边界

- Hermes 候选：v0.19.0 / Git tag v2026.7.20；
- Python 3.10：package/core/artifact-only；完整 Hermes v0.19.0 组合不支持 Python 3.10；
- Python 3.11–3.12：完整 Hermes 候选支持范围；
- real Hermes E2E 属于 COMPAT-001 / M4 / G3；
- reproducibility、SBOM、provenance 属于 REL-006；
- Runtime 当前 9 real Tools，目标 10；不得添加 placeholder memory_store；
- 当前 6 strict XFAIL owners：SES-001、AUD-001、CON-001×3、MEM-002；
- 不提前合入 master，不提前 Tag/Release，不发布 PyPI；
- 不访问真实 HOME、DB、Memory、Secret；
- 不弱化 PID、process identity、exact argv、symlink、traversal、rollback 或 destructive-operation 防线。

七、执行纪律

- 一次只实施一个 Work ID 或评估一个 Gate；
- 最新 develop → 专用分支 → Draft PR → TDD Red → 最小实现 → Required CI → Code Review → unresolved threads 0 → expected-Head Squash Merge；
- 禁止 skip、弱化断言、删除测试、隐藏 XFAIL/XPASS；
- 每个 Work ID 建立 docs/testing/evidence/<WORK-ID>.md；
- 每个有意义批次立即 push；
- 上下文腐烂或工具循环时，先 commit、push、更新 Evidence/Status/Handoff 和 Issue，再交接新会话；不得留下仅存在于临时容器的代码。

持续目标：SES-001 → PRIV-001 → G2 → M3 → M4/G3 → master RC → v3.0.0-beta.1 → real Beta feedback/G4 → Stable prep/SOAK/G5 → v3.0.0。
```
