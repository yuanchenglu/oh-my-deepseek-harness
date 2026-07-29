# 新会话交接提示词

```text
你继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格、串行、持续完成 Open-source Beta → Stable 全计划。除真实 Owner 外部门禁外，不等待“继续”。每完成一个 Work ID 或 Gate，读取最新远程 develop，并启动下一个唯一合法任务。

一、远程唯一事实源

启动后读取最新 develop、master、开放 PR、开放 canonical Issues、最近 CI，以及：

- docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md（v2.3.11 或更新）；
- docs/roadmap/EXECUTION_STATUS.md；
- docs/roadmap/SESSION_HANDOFF_PROMPT.md；
- docs/roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md；
- docs/testing/TEST_PLAN.md；
- docs/testing/evidence/GATE-G1.md；
- docs/testing/evidence/CTX-001.md；
- docs/testing/evidence/CTX-002.md；
- docs/testing/evidence/CTX-003.md；
- docs/traceability/RELEASE_TRACEABILITY.md；
- docs/compatibility/HERMES_MATRIX.md。

交接快照与 GitHub 事实冲突时，以远程事实为准并同步修正文档。

二、当前事实快照

- develop：0eb68d7077a0b8b8898b61f20bb209175619ec42
- master：398701c5cf6495180a7a7566f09921cf126a054a
- 固定 Work ID：48
- Complete：19/48（39.6%）
- In progress：0/48
- Not started / dependency blocked：29/48
- M0：Complete
- G0：PASS
- M1：8/8 Complete
- G1：PASS
- CTX-001、CTX-002、CTX-003：Complete
- 产品成熟度：Experimental Preview
- master、Tag、GitHub Release、PyPI 尚未进入发布阶段
- PyPI 按 REL-005 保持禁用

三、CTX-003 完成事实

- Issue #28：Closed / completed
- PR #85：Merged
- TDD red：Run #214 / ID 30415339296
- Code acceptance：Run #217 / ID 30415608111
- Final Head：34fd2811596aab58c74a55212a5abb2d70f7e22b
- Final CI：Run #218 / ID 30415808432
- Squash：0eb68d7077a0b8b8898b61f20bb209175619ec42
- Python 3.10/3.11/3.12：每版本 243 tests、0 failures、0 errors、6 strict XFAIL
- stable IDs、hard constraints、latest request、Tool Pair 不变量全部 PASS
- 64 组 seeded property sequences，0 counterexamples
- `CR-P0-004`、`XF-CTX-003`：Closed

四、当前唯一合法任务：CTX-004 #29

完成 docs-only CTX-003 post-merge closure 后：

1. 读取 Issue #29 与评论；
2. 核对 `FR-CONTEXT-001–002/008–010/013` 与 `TC-CTX-001–002/011–013`；
3. 从最新 develop 创建 `fix/ctx-004-compression-rollback-invariants`；
4. 评论执行开始、基线、范围和 exclusions；
5. 建立 threshold/no-op、成功压缩、Token 不下降 rollback、输入不变、Session Summary 状态隔离测试；
6. 创建 Draft PR；
7. 使用 fake provider、synthetic sessions 与 deterministic token accounting；
8. 只实现最小正确的压缩事务与 rollback 不变量；
9. 不提前实施 SES-001、PRIV-001；
10. 创建 docs/testing/evidence/CTX-004.md；
11. Final Head Required CI 全绿后 expected-Head Squash Merge；
12. 关闭 #29 并自动进入 SES-001。

五、固定顺序

CTX-004 → SES-001 → PRIV-001 → G2

SES-001 的硬依赖已满足，但禁止并行启动。

六、固定边界

- Hermes 候选：v0.19.0 / Git tag v2026.7.20；
- Python 3.10 remains package/core/artifact-only after PKG-001; the complete Hermes v0.19.0 integration combination does not support Python 3.10；
- real Hermes E2E 属于 COMPAT-001 / M4 / G3；
- reproducibility、SBOM、provenance 属于 REL-006；
- Runtime 当前 9 Tools，目标 10；不得添加 placeholder memory_store；
- 当前 6 strict XFAIL owners：SES-001、AUD-001、CON-001×3、MEM-002；
- 不合入 master，不提前 Tag/Release，不发布 PyPI；
- 不访问真实 HOME、DB、Memory、Secret；
- 不弱化 PID、symlink、traversal、rollback 或 destructive-operation 防线。

七、执行纪律

- 一次只实施一个 Work ID 或评估一个 Gate；
- 专用分支 → Draft PR → Required CI → Ready → expected-Head Squash Merge develop；
- 先失败测试，再最小正确实现；
- 禁止 skip、弱化断言、删除测试、隐藏 XFAIL/XPASS；
- 每个 Work ID 建立 docs/testing/evidence/<WORK-ID>.md；
- 每个有意义批次立即 push；
- 合并后自动读取最新 develop 并继续。

持续目标：CTX-004 → M2/G2 → M3 → M4/G3 → master RC → v3.0.0-beta.1 → Beta feedback/G4 → Stable prep/soak/G5 → v3.0.0。
```
