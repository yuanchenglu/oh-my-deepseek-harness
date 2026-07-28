# 新会话交接提示词

将下面完整提示词复制到新会话。新会话不得依赖旧容器、旧工作区、旧缓存或未推送文件，只以 GitHub 远程状态为准。

```text
你现在继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格、串行、持续完成 Open-source Beta → Stable 发布计划。除真实 Owner 外部门禁外，不等待用户发送“继续”。每完成一个 Work ID 或 Gate，重新读取最新远程 develop，并自动启动下一个依赖已经满足的唯一合法任务。

一、启动后必须先核对远程事实

1. 读取最新 develop Head、master Head、开放 PR、开放 canonical Issues 和最近 CI。
2. 读取：
   - docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md（目标版本 v2.3.6 或更新）
   - docs/roadmap/EXECUTION_STATUS.md
   - docs/roadmap/SESSION_HANDOFF_PROMPT.md
   - docs/roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md
   - docs/testing/TEST_PLAN.md
   - docs/testing/evidence/GATE-G1.md
   - docs/testing/evidence/QA-ART-001.md
   - docs/traceability/RELEASE_TRACEABILITY.md
   - docs/compatibility/HERMES_MATRIX.md
3. 核对当前 G1 Gate PR #77 是否已合入 develop。
4. 交接快照与 GitHub 当前事实冲突时，以远程事实为准并同步修正文档。

二、当前已知事实快照

- 接管审计基线：develop@8260c671786aa2ea994d61e6bde09ad57992ef36
- master@398701c5cf6495180a7a7566f09921cf126a054a
- 固定 Work ID：48
- Complete：16/48（33.3%）
- In progress：0/48
- Not started / dependency blocked：32/48
- M0：Complete
- G0：PASS
- M1：8/8 Complete
- 产品成熟度：Experimental Preview
- master 尚未进入当前发布周期
- Tag / GitHub Release / PyPI 均未执行
- PyPI 按 REL-005 保持禁用

M1 已完成：

PKG-001 → PKG-002 → RUN-001 → RUN-002 → INS-001 → INS-002 → INS-003 → QA-ART-001

QA-ART-001：

- Issue #25：原实现已 Closed / completed；G1 FAIL 后需重新开启 remediation
- PR #74：merged
- Squash：7adbb0cb00e781e31fee0ee5d360f52c4bdce5eb
- Final CI：Run #166 / ID 30343118259
- Python 3.10/3.11/3.12：每版本 230 tests、0 failures、0 errors、9 strict XFAIL
- 每个 job artifact JUnit：1 test、0 failures、0 errors

三、G1 独立评估结论

G1 Evidence：docs/testing/evidence/GATE-G1.md
G1 PR：#77
结论：FAIL
Checklist：8 PASS / 2 FAIL / 0 BLOCKED

失败项只有：

1. Required artifact path 只构建 wheel，没有从同一 clean snapshot 构建并验证 sdist；
2. Required artifact path 没有执行 python -m twine check dist/*。

已 PASS 的 G1 条款：

- wheel 包含 Server、Plugin、Context、YAML/策略与 package data；
- 源码目录外可导入公共 package；
- wheel 不依赖源码 symlink 或仓库相对路径；
- Console Script 可启动、检查、停止 Server；
- /health、/ready、/version 满足契约；
- 空 HOME 完成 pip install → install → doctor → smoke → ordinary uninstall → pip uninstall；
- 重复安装、端口占用、安装中断、卸载保留数据通过；
- 安装和测试不读取或修改真实 ~/.hermes。

四、当前唯一合法任务

如果 PR #77 尚未合入：

1. 核对其最终 Head 和 Required CI；
2. 必要时修复文档/CI；
3. Ready 后使用 expected Head Squash Merge；
4. 完成 G1 FAIL post-merge 事实收口。

PR #77 合入后：

1. 重新开启 canonical Issue #25；
2. 评论 G1 两个失败条款、最新 develop 基线、范围和 exclusions；
3. 从最新 develop 创建：test/qa-art-001-sdist-twine-remediation；
4. 建立 Draft PR；
5. 只补齐 QA artifact 范围：
   - 同一 clean git archive snapshot 构建 wheel + sdist；
   - 分别记录 SHA256 和 inventory；
   - 对 dist/* 执行 python -m twine check；
   - 保持 final wheel 的 source-external install/Doctor/Server/upgrade/uninstall lifecycle；
   - Python 3.10/3.11/3.12 Required jobs 上传 artifacts、logs 和 JUnit；
6. 不借此修改 Context、Session、Tool/API/DB、Memory、Plan、真实 Hermes、Migration 或发布逻辑；
7. Required CI 全绿后 Squash Merge并关闭 #25；
8. 完成 QA-ART-001 remediation post-merge Evidence；
9. 从最新 develop 创建新的独立 G1 re-evaluation；
10. 只有 G1 明确 PASS 后，才启动 M2 的唯一合法 Work ID。

五、G1 解释边界

- 正式不可变 Beta Tag 只能在精确 master artifact 和最终 test-release 通过后创建；G1 使用冻结 Commit 的 clean archive，不得提前创建 Tag。
- 三个独立 wheel SHA 不同不是 G1 blocker；reproducibility、SBOM、provenance 属于 REL-006。
- 真实 Hermes discovery/enable/Hook/ContextEngine/Tool E2E 属于 COMPAT-001（M4/G3），不属于 G1，否则形成循环依赖。
- Python 3.10 只证明 package/core/artifact lifecycle 和完整 Hermes 组合的预期拒绝；Python 3.11–3.12 才是完整 Hermes v0.19.0 候选组合。
- 当前 Runtime 仍为 9 Tools，目标为 10；不得提前添加 placeholder memory_store。
- 9 个 strict XFAIL 均有 canonical owner：CTX-001、CTX-002、CTX-003、SES-001、AUD-001、CON-001×3、MEM-002。

六、单 Work ID / Gate 执行纪律

1. 一次只实施一个 Work ID 或评估一个 Gate。
2. 从最新 develop 创建专用分支和 Draft PR。
3. 读取 canonical Issue 全文、评论、硬依赖、授权路径、FR/CR/Test ID。
4. 先建立失败测试或可证伪证据，再做最小正确实现。
5. 不得通过 skip、弱化断言、隐藏 XFAIL/XPASS 或删除测试伪造绿色。
6. 每个 Work ID 建立 docs/testing/evidence/<WORK-ID>.md。
7. 同一最终 PR Head 的 Required Checks 全绿后，使用 expected Head Squash Merge。
8. 合并后关闭 Issue并记录 Squash Commit、CI、Evidence、计划、状态、Traceability 和 handoff。
9. 自动读取最新 develop并启动下一个唯一合法任务。

七、开发流程规范

适用项目：deepseekagent、deepcode、deepseek_runtime、llm-harness-agent、oh-my-deepseek-harness
Remote：https://github.com/yuanchenglu/<项目名>.git
开发分支：develop
发布分支：master

第一优先：PR 流程

- 专用分支 → Draft PR → Required CI → Ready → Squash Merge develop。
- PR 标题和描述说明 Work ID/Gate、变更、原因、风险、验证和 exclusions。

第二优先：直推 develop 兜底

只有 PR 流程持续因平台、规则或当前环境无法解决的故障阻塞时才允许；不得直推 master，不得绕过代码缺陷、安全、测试或 Gate。

直推 Commit 必须包含：

<type>(<scope>): <变更说明>

## 问题原因
<PR/CI 无法完成的真实根因>

## 技术债务
- <遗留事项>

技术债务写入 docs/TECH_DEBT.md，格式：
[日期] 描述 | 遗留原因 | 状态

八、远程持久化

- 不允许唯一代码、文档、日志或 Evidence 只留在临时容器。
- 每个有意义批次立即 Commit 和 push。
- 暂时不能合入 develop 时，至少推送专用远程分支并建立 PR。
- 失败日志、根因和后续动作写入 Issue、PR 或 Evidence。
- 新会话只相信远程。

九、严格边界

G1 PASS 前：

- 不启动 CTX-001、SES-001 或其他 M2；
- 不合入 master；
- 不创建 Tag 或 GitHub Release；
- 不发布 PyPI；
- 不声称 Public Beta Ready；
- 不把 fake Hermes 描述为真实 Hermes E2E；
- 不读取或修改真实 HOME、DB、Memory、Secret；
- 不向无法证明归属的 PID 发送信号；
- 不弱化 symlink、traversal、rollback 或 destructive-operation 防线。

十、持续目标

G1 remediation → G1 PASS → M2/G2 → M3 → M4/G3 → master RC → v3.0.0-beta.1 → Beta feedback/G4 → Stable prep/soak/G5 → v3.0.0。

只有 48 Work ID、G0–G5、Beta、Stable、发布后验证、Evidence、Traceability 和远程持久化全部闭环，才允许声明 Plan 完成。
```
