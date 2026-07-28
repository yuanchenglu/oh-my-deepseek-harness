# 新会话交接提示词

```text
你继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格、串行、持续完成 Open-source Beta → Stable 全计划。除真实 Owner 外部门禁外，不等待“继续”。每完成一个 Work ID 或 Gate，重新读取最新远程 develop，并启动下一个唯一合法任务。

一、远程唯一事实源

启动后读取：

1. 最新 develop、master、开放 PR、开放 canonical Issues、最近 CI；
2. docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md（v2.3.8 或更新）；
3. docs/roadmap/EXECUTION_STATUS.md；
4. docs/roadmap/SESSION_HANDOFF_PROMPT.md；
5. docs/roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md；
6. docs/testing/TEST_PLAN.md；
7. docs/testing/evidence/GATE-G1.md；
8. docs/testing/evidence/QA-ART-001.md；
9. docs/traceability/RELEASE_TRACEABILITY.md；
10. docs/compatibility/HERMES_MATRIX.md。

交接快照与 GitHub 事实冲突时，以远程事实为准并同步修正文档。

二、当前事实快照

- develop：b0b9d2e0337a9f40f2abcdb0f91ce8b2865ea765
- master：398701c5cf6495180a7a7566f09921cf126a054a
- 固定 Work ID：48
- Complete：16/48（33.3%）
- In progress：0/48
- Not started / dependency blocked：32/48
- M0：Complete
- G0：PASS
- M1：8/8 Complete
- G1：PASS
- 产品成熟度：Experimental Preview
- master 尚未进入当前发布周期
- Tag / GitHub Release / PyPI 均未执行
- PyPI 按 REL-005 保持禁用

三、G1 审计轨迹

初始评估：

- PR #77
- Squash：9a8c3a8f7b94111d626ec9319612e0574de04c84
- 结论：FAIL — 8 PASS / 2 FAIL / 0 BLOCKED
- 失败：缺 sdist；缺 python -m twine check dist/*

QA-ART-001 remediation：

- Issue #25：Closed / completed
- PR #78：Merged
- Final Head：531aa0e3fd327dc9a096668432ebd1d0b2bff43b
- Final CI：Run #184 / ID 30382668758
- Squash：5ebb3a0c9b44cd5f2a2be789f9224740d47894f8
- Python 3.10/3.11/3.12：每版本 231 tests、0 failures、0 errors、9 strict XFAIL
- wheel：39 files；sdist：75 files；twine wheel+sdist PASS

G1 PASS 复评：

- PR #79：Merged
- Final Head：e6e39b54040c5deba12d474daf596f7da4272a7c
- Final CI：Run #193 / ID 30384094675
- Python 3.10/3.11/3.12：success
- Squash：b0b9d2e0337a9f40f2abcdb0f91ce8b2865ea765
- 结论：PASS — 10 PASS / 0 FAIL / 0 BLOCKED

四、当前唯一合法任务：CTX-001 #26

完成 docs-only G1 post-merge closure 后：

1. 读取 Issue #26 全文与评论；
2. 核对依赖、授权路径、CR-P0-002、TC-CTX-003；
3. 从最新 develop 创建 fix/ctx-001-merge-uniqueness；
4. 评论执行开始、基线、范围与 exclusions；
5. 将 TC-CTX-003 从 strict XFAIL 转为普通失败回归；
6. 创建 Draft PR；
7. 最小修复 Merge 分支重复尾消息装配；
8. 不提前实施 CTX-002/003/004、SES-001、PRIV-001；
9. 创建 docs/testing/evidence/CTX-001.md；
10. 同一最终 Head Required CI 全绿后 expected-Head Squash Merge；
11. 关闭 #26，更新计划、状态、Traceability、handoff；
12. 自动进入 CTX-002。

五、M2 固定串行顺序

CTX-001 → CTX-002 → CTX-003 → CTX-004 → SES-001 → PRIV-001 → G2

SES-001 的硬依赖已满足，但禁止并行启动。

六、固定边界

- Hermes 候选：v0.19.0 / Git tag v2026.7.20；
- Python 3.10 仅 package/core/artifact lifecycle，完整 Hermes 候选矩阵为 3.11–3.12；
- real Hermes E2E 属于 COMPAT-001 / M4 / G3；
- reproducibility、SBOM、provenance 属于 REL-006；
- Runtime 当前 9 Tools，目标 10；不得添加 placeholder memory_store；
- 9 strict XFAIL owners：CTX-001、CTX-002、CTX-003、SES-001、AUD-001、CON-001×3、MEM-002；
- 不合入 master，不创建 Tag/Release，不发布 PyPI；
- 不访问真实 HOME、DB、Memory、Secret；
- 不弱化 PID、symlink、traversal、rollback 或 destructive-operation 防线。

七、执行纪律

- 一次只实施一个 Work ID 或评估一个 Gate；
- 专用分支 → Draft PR → Required CI → Ready → expected-Head Squash Merge develop；
- 先失败测试，再最小正确实现；
- 禁止 skip、弱化断言、删除测试、隐藏 XFAIL/XPASS；
- 每个 Work ID 建立 docs/testing/evidence/<WORK-ID>.md；
- 每个有意义批次立即 push，任何唯一成果不得只留在临时容器；
- 合并后自动读取最新 develop 并继续下一个唯一任务。

持续目标：CTX-001 → M2/G2 → M3 → M4/G3 → master RC → v3.0.0-beta.1 → Beta feedback/G4 → Stable prep/soak/G5 → v3.0.0。
```
