# 新会话交接提示词

将下面完整提示词复制到新会话。新会话不得依赖旧容器、旧工作区、旧缓存或未推送文件，只以 GitHub 远程状态为准。

```text
你现在继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格、串行、持续完成 Open-source Beta → Stable 发布计划。除真实 Owner 外部门禁外，不等待用户发送“继续”。每完成一个 Work ID 或 Gate，重新读取最新远程 develop，并自动启动下一个依赖已经满足的唯一合法任务。

一、启动后先核对远程事实

1. 读取最新 develop、master、开放 PR、开放 canonical Issues 与最近 CI。
2. 读取：
   - docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md（目标版本 v2.3.7 或更新）
   - docs/roadmap/EXECUTION_STATUS.md
   - docs/roadmap/SESSION_HANDOFF_PROMPT.md
   - docs/roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md
   - docs/testing/TEST_PLAN.md
   - docs/testing/evidence/GATE-G1.md
   - docs/testing/evidence/QA-ART-001.md
   - docs/traceability/RELEASE_TRACEABILITY.md
   - docs/compatibility/HERMES_MATRIX.md
3. 核对 G1 PASS 复评 PR #79 的真实状态。
4. 交接快照与远程冲突时，以 GitHub 事实为准并同步修正文档。

二、当前已知事实快照

- G1 复评基线：develop@5ebb3a0c9b44cd5f2a2be789f9224740d47894f8
- master@398701c5cf6495180a7a7566f09921cf126a054a
- 固定 Work ID：48
- Complete：16/48（33.3%）
- In progress：0/48
- Not started / dependency blocked：32/48
- M0：Complete
- G0：PASS
- M1：8/8 Complete
- G1：PASS（PR #79 合并前为复评候选事实；必须核对远程）
- 产品成熟度：Experimental Preview
- master 尚未进入当前发布周期
- Tag / GitHub Release / PyPI 均未执行
- PyPI 按 REL-005 保持禁用

三、G1 审计轨迹

初始评估：

- PR #77
- 结论：FAIL — 8 PASS / 2 FAIL / 0 BLOCKED
- Squash：9a8c3a8f7b94111d626ec9319612e0574de04c84
- 失败项：缺 sdist；缺 python -m twine check dist/*

QA-ART-001 remediation：

- Issue #25：Closed / completed
- PR #78：Merged
- Final PR Head：531aa0e3fd327dc9a096668432ebd1d0b2bff43b
- Final CI：Run #184 / ID 30382668758
- Squash：5ebb3a0c9b44cd5f2a2be789f9224740d47894f8
- Python 3.10/3.11/3.12：每版本 231 tests、0 failures、0 errors、9 strict XFAIL
- 每个 job artifact JUnit：1 / 0 failures / 0 errors / 0 skipped
- wheel：39 files
- sdist：75 files
- twine：每版本 wheel + sdist PASS

G1 独立复评：

- PR #79
- Evidence：docs/testing/evidence/GATE-G1.md
- 结论：PASS — 10 PASS / 0 FAIL / 0 BLOCKED
- G1 只解锁 M2，不代表 Public Beta、master、Tag、Release 或 publication ready

四、当前唯一合法任务

如果 PR #79 尚未合入：

1. 核对最终 Head 与 Required CI；
2. 修复任何真实失败；
3. Mark Ready；
4. 使用 expected Head Squash Merge；
5. 读取最新 develop。

PR #79 合入后，只启动 CTX-001 #26：

1. 读取 Issue #26 全文与评论；
2. 核对依赖、授权路径、CR-P0-002、TC-CTX-003；
3. 从最新 develop 创建 fix/ctx-001-merge-uniqueness；
4. 评论执行开始、基线、范围与 exclusions；
5. 建立 Draft PR；
6. 将 TC-CTX-003 从 strict XFAIL 转为普通失败回归；
7. 最小修复 Merge 分支重复尾消息装配；
8. 不提前实施 CTX-002/003/004、SES-001 或 PRIV-001；
9. 创建 docs/testing/evidence/CTX-001.md；
10. 同一最终 Head Required CI 全绿后 expected-Head Squash Merge；
11. 关闭 #26，更新计划/状态/Traceability/handoff；
12. 自动进入 CTX-002。

五、M2 固定串行顺序

归档硬依赖允许 CTX-001 与 SES-001 同时具备入口条件。为满足单一 Work ID 纪律，当前计划按 canonical 表格与 Issue 顺序固定：

CTX-001 → CTX-002 → CTX-003 → CTX-004 → SES-001 → PRIV-001 → G2

不得并行启动 SES-001。

六、G1 边界

- 正式 Beta Tag 只能在精确 master artifact 与最终 test-release 后创建。
- wheel/sdist 跨 job hash 不同不属于 G1；REL-006 负责 reproducibility、SBOM、provenance。
- 真实 Hermes E2E 属于 COMPAT-001（M4/G3），不属于 G1。
- Python 3.10 只证明 package/core/artifact lifecycle 与完整 Hermes 组合的预期拒绝；完整候选矩阵是 Python 3.11–3.12。
- 当前 Runtime 仍为 9 Tools，目标 10；不得添加 placeholder memory_store。
- 9 个 strict XFAIL owners：CTX-001、CTX-002、CTX-003、SES-001、AUD-001、CON-001×3、MEM-002。

七、单 Work ID / Gate 纪律

1. 一次只实施一个 Work ID 或评估一个 Gate。
2. 从最新 develop 创建专用分支与 Draft PR。
3. 读取 canonical Issue、评论、硬依赖、授权路径、FR/CR/Test ID。
4. 先建立普通失败测试或可证伪证据，再做最小正确实现。
5. 禁止 skip、弱化断言、删除测试、隐藏 XFAIL/XPASS。
6. 每个 Work ID 建立 docs/testing/evidence/<WORK-ID>.md。
7. 同一最终 Head Required Checks 全绿后使用 expected Head Squash Merge。
8. 合并后关闭 Issue，记录 Squash、CI、Evidence、计划、状态、Traceability 与 handoff。
9. 自动读取最新 develop 并启动下一个唯一任务。

八、开发流程

适用项目：deepseekagent、deepcode、deepseek_runtime、llm-harness-agent、oh-my-deepseek-harness
Remote：https://github.com/yuanchenglu/<项目名>.git
开发分支：develop
发布分支：master

优先走：专用分支 → Draft PR → Required CI → Ready → Squash Merge develop。
只有平台/权限/规则导致 PR 路径在当前环境确实无法解决时，才允许按规范直推 develop；不得直推 master，不得用直推绕过缺陷、安全、测试或 Gate。

九、远程持久化

- 不允许唯一代码、文档、日志或 Evidence 只留在临时容器。
- 每个有意义批次立即 Commit 和 push。
- 暂时不能合入时，至少保留远程分支与 PR。
- 失败日志、根因和下一步写入 Issue、PR 或 Evidence。
- 新会话只相信远程。

十、严格边界

- 不并行启动 Work ID；
- 不提前实施后续 Context/Session/Privacy；
- 不合入 master；
- 不创建 Tag 或 GitHub Release；
- 不发布 PyPI；
- 不声称 Public Beta Ready；
- 不把 fake Hermes 描述为真实 Hermes E2E；
- 不读取或修改真实 HOME、DB、Memory、Secret；
- 不向无法证明归属的 PID 发信号；
- 不弱化 symlink、traversal、rollback 或 destructive-operation 防线。

十一、持续目标

CTX-001 → CTX-002 → CTX-003 → CTX-004 → SES-001 → PRIV-001 → G2 → M3 → M4/G3 → master RC → v3.0.0-beta.1 → Beta feedback/G4 → Stable prep/soak/G5 → v3.0.0。

只有 48 Work ID、G0–G5、Beta、Stable、发布后验证、Evidence、Traceability 与远程持久化全部闭环，才允许声明 Plan 完成。
```
