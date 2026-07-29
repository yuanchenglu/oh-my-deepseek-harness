# 新会话交接提示词

```text
你继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格、串行、持续完成 Open-source Beta → Stable 全计划。除真实 Owner 外部门禁外，不等待“继续”。每完成一个 Work ID 或 Gate，读取最新远程 develop，并启动下一个唯一合法任务。

一、远程唯一事实源

启动后读取最新 develop、master、开放 PR、开放 canonical Issues、最近 CI，以及：

- docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md（v2.3.10 或更新）；
- docs/roadmap/EXECUTION_STATUS.md；
- docs/roadmap/SESSION_HANDOFF_PROMPT.md；
- docs/roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md；
- docs/testing/TEST_PLAN.md；
- docs/testing/evidence/GATE-G1.md；
- docs/testing/evidence/CTX-001.md；
- docs/testing/evidence/CTX-002.md；
- docs/traceability/RELEASE_TRACEABILITY.md；
- docs/compatibility/HERMES_MATRIX.md。

交接快照与 GitHub 事实冲突时，以远程事实为准并同步修正文档。

二、当前事实快照

- develop：bf4ab49e1b3c5bbe752931d19460ad2de4243a6f
- master：398701c5cf6495180a7a7566f09921cf126a054a
- 固定 Work ID：48
- Complete：18/48（37.5%）
- In progress：0/48
- Not started / dependency blocked：30/48
- M0：Complete
- G0：PASS
- M1：8/8 Complete
- G1：PASS
- CTX-001、CTX-002：Complete
- 产品成熟度：Experimental Preview
- master、Tag、GitHub Release、PyPI 尚未进入发布阶段
- PyPI 按 REL-005 保持禁用

三、CTX-002 完成事实

- Issue #27：Closed / completed
- PR #83：Merged
- TDD red：Run #207 / ID 30414160582
- Code acceptance：Run #208 / ID 30414258095
- Final Head：5b16121b1366180e640f8ca37f858f0464030453
- Final CI：Run #209 / ID 30414491094
- Squash：bf4ab49e1b3c5bbe752931d19460ad2de4243a6f
- Python 3.10/3.11/3.12：每版本 239 tests、0 failures、0 errors、7 strict XFAIL
- timeout、exception、None/empty/whitespace、missing-key response 均返回原输入列表
- 不插入 placeholder；模拟 Secret 和 prompt fragment 不进入日志
- `CR-P0-003`、`XF-CTX-002`：Closed

四、当前唯一合法任务：CTX-003 #28

完成 docs-only CTX-002 post-merge closure 后：

1. 读取 Issue #28 与评论；
2. 核对 `CR-P0-004`、`FR-CONTEXT-003–005/009`、`TC-CTX-007–009/014`、`XF-CTX-003`；
3. 从最新 develop 创建 `fix/ctx-003-protected-message-integrity`；
4. 评论执行开始、基线、范围和 exclusions；
5. 将 hard-constraint strict XFAIL 转为普通失败测试；
6. 创建 Draft PR；
7. 实现 stable message IDs、protected-message classification 与 Tool Call/Result pair validation；
8. hard constraints 和 latest requests 必须逐字保留，每个 protected/latest ID 恰好一次；
9. Tool pairs 在生成序列中保持合法；
10. 增加 property tests，零 minimized counterexamples；
11. 不提前实施 CTX-004、SES-001、PRIV-001；
12. 创建 docs/testing/evidence/CTX-003.md；
13. Final Head Required CI 全绿后 expected-Head Squash Merge；
14. 关闭 #28 并自动进入 CTX-004。

五、固定顺序

CTX-003 → CTX-004 → SES-001 → PRIV-001 → G2

SES-001 的硬依赖已满足，但禁止并行启动。

六、固定边界

- Hermes 候选：v0.19.0 / Git tag v2026.7.20；
- Python 3.10 remains package/core/artifact-only after PKG-001; the complete Hermes v0.19.0 integration combination does not support Python 3.10；
- real Hermes E2E 属于 COMPAT-001 / M4 / G3；
- reproducibility、SBOM、provenance 属于 REL-006；
- Runtime 当前 9 Tools，目标 10；不得添加 placeholder memory_store；
- 当前 7 strict XFAIL owners：CTX-003、SES-001、AUD-001、CON-001×3、MEM-002；
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

持续目标：CTX-003 → M2/G2 → M3 → M4/G3 → master RC → v3.0.0-beta.1 → Beta feedback/G4 → Stable prep/soak/G5 → v3.0.0。
```
