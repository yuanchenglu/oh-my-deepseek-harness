# 新会话交接提示词

将下面完整提示词复制到新会话。新会话不得依赖旧容器、旧工作区、旧缓存或未提交文件，只以 GitHub 远程状态为准。

```text
你现在继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格继续 Open-source Beta 发布计划。当前 M1 已完成 8/8；下一步只能执行独立 G1 Gate 评估。G1 未形成明确 PASS Evidence 前，不得启动 CTX-001 #26、SES-001 #30 或其他 G1 后继任务，也不得合入 master、创建 Tag/Release 或发布 PyPI。

一、启动后必须先核对远程事实

1. 读取最新 develop Head，不得根据本提示词猜测。
2. 读取：
   - docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md（目标版本 v2.3.5）
   - docs/roadmap/EXECUTION_STATUS.md
   - docs/roadmap/SESSION_HANDOFF_PROMPT.md
   - docs/roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md
   - docs/testing/TEST_PLAN.md
   - docs/testing/evidence/PKG-001.md
   - docs/testing/evidence/PKG-002.md
   - docs/testing/evidence/RUN-001.md
   - docs/testing/evidence/RUN-002.md
   - docs/testing/evidence/INS-001.md
   - docs/testing/evidence/INS-002.md
   - docs/testing/evidence/INS-003.md
   - docs/testing/evidence/QA-ART-001.md
   - docs/traceability/RELEASE_TRACEABILITY.md
   - docs/compatibility/HERMES_MATRIX.md
3. 核对 QA-ART-001：
   - Canonical Issue：#25，必须 Closed / completed；
   - Delivery PR：#74，必须 merged；
   - Squash Commit：7adbb0cb00e781e31fee0ee5d360f52c4bdce5eb；
   - Code acceptance Head：81195f844b681e85ccf2c0a15fc4935b2b396ed6；
   - Final PR Head：2a0263b3fe5dec75f6dae89203ecda6b6275ec9f；
   - Code CI：Run #161 / ID 30342161995；
   - Final PR-head CI：Run #166 / ID 30343118259。
4. 核对 QA-ART-001 post-merge 文档收口是否已合入 develop。
5. 若 PR #74、Issue #25 或 post-merge 文档收口任一未完成，只允许完成该收口，不得建立 G1 结论。
6. 所有远程事实与提示词冲突时，以 GitHub 当前远程事实为准，并修正文档。

二、当前真实进展

固定分母：48 个 Work ID。

- Complete：16/48（33.3%）
- In progress：0/48
- Not started / dependency blocked：32/48（66.7%）
- M0：完成
- G0：PASS
- M1：8/8 Complete
- G1：READY FOR SEPARATE EVALUATION，尚未判定
- 产品成熟度：Experimental Preview
- master：未合并
- Tag / GitHub Release / PyPI：均未执行

M1 已完成链路：

PKG-001 → PKG-002 → RUN-001 → RUN-002 → INS-001 → INS-002 → INS-003 → QA-ART-001

QA-ART-001 最终验收：

- Python 3.10：230 tests / 0 failures / 0 errors / 9 strict XFAIL
- Python 3.11：230 tests / 0 failures / 0 errors / 9 strict XFAIL
- Python 3.12：230 tests / 0 failures / 0 errors / 9 strict XFAIL
- 每个 job 另有 artifact JUnit：1 test / 0 failures / 0 errors / 0 skipped

已证明：

- clean git archive HEAD 构建最终 3.0.0b1 wheel；
- fresh non-editable venv 只安装 wheel distribution 与声明依赖；
- 空 PYTHONPATH、源码树外 cwd、module origin 与 sys.path 均无源码污染；
- wheel 39 files，不包含 plugins/、mcp/、tests/；
- install dry-run、clean install、Doctor、Server health/ready/version、POST /memory/tag；
- Python 3.10 按支持分层由 Doctor 预期拒绝完整 Hermes 组合；
- Python 3.11/3.12 fake Hermes 0.19.0 诊断通过；
- same-version upgrade 幂等并复用 PID；
- ordinary uninstall 保留 distribution/config/DB，只打印精确 pip uninstall command；
- 实际 pip uninstall 仅由测试脚本在临时 venv 执行；
- fake Secret 未进入上传文本证据；
- 每个 Required job 上传 wheel、SHA256、inventory、JSON/log 与 JUnit。

三个独立 job 的 wheel SHA256 不同。QA-ART-001 不声明 reproducible-build PASS；最终 reproducibility/provenance 仍属于 REL-006，除非 G1 原始条款明确将其前置。

三、当前唯一任务：独立 G1 Gate 评估

G1 不是 Work ID 数量统计。必须先提取规范 Gate 条款、建立 checklist，再写结论。结论只能为 PASS、FAIL 或 BLOCKED。

至少逐条核对：

1. M1 八个 Work ID 的 Issue、PR、Squash Commit、Evidence、Required CI 是否全部闭环；
2. CR-P0-001 是否已经由 M1 证据关闭，是否仍有属于 G1 的开放 P0 blocker；
3. package/import/App Factory/Supervisor/install/Doctor/upgrade/recover/uninstall/purge/final-wheel 证据是否完整且来源明确；
4. 9 个 strict XFAIL 是否全部有后续 canonical owner，M1 是否没有无主 XFAIL；
5. Python 支持分层是否一致：3.10 仅 package/core/artifact lifecycle，3.11–3.12 才是完整 Hermes v0.19.0 候选组合；
6. QA-ART-001 wheel hash 差异是否是 G1 blocker，必须按 G1 原始条款判断，不得凭主观提前 REL-006；
7. 真实 Hermes discovery/selection/Hook/ContextEngine/Tool E2E 是否属于 G1，必须按主计划、归档和 HERMES_MATRIX 判断；
8. 是否存在真实 HOME/DB/Memory/Secret 污染、foreign PID、symlink/traversal、destructive-operation 或 rollback 未闭环风险；
9. Gate Evidence 必须为每条标准列出：规范原文/含义、证据、判定、残余风险和 exclusions；
10. G1 PASS 只解锁 M2 的合法入口，不代表 Public Beta、master 或 publication ready。

四、G1 执行顺序

1. 从最新 develop 创建专用分支，建议：docs/gate-g1-evaluation。
2. 立即建立 Draft PR，PR 描述只陈述评估范围，不预写 PASS。
3. 读取主计划、v2.2 归档、Test Plan、Traceability、HERMES_MATRIX 和所有 M1 Evidence。
4. 建立逐条 G1 checklist，先证据后结论。
5. 检查开放 Issues、P0 blockers、XFAIL owners、Python/Hermes 分层和 artifact evidence。
6. 创建 docs/testing/evidence/GATE-G1.md。
7. 同步：
   - docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md
   - docs/roadmap/EXECUTION_STATUS.md
   - docs/roadmap/SESSION_HANDOFF_PROMPT.md
   - docs/traceability/RELEASE_TRACEABILITY.md
8. 运行 Required CI：test (3.10)、test (3.11)、test (3.12)。每个 job 仍包含源码外 final-wheel lifecycle。
9. CI 全绿后，根据证据将 G1 判为 PASS、FAIL 或 BLOCKED，并清楚列出 exclusions。
10. 通过 PR 合入 develop，随后完成 Gate post-merge 事实收口。
11. 只有 G1 明确 PASS 后，才按硬依赖选择下一个唯一 Work ID；不得同时启动多个 M2 任务。

五、开发流程规范（适用于以下 5 个项目）

适用项目：

- deepseekagent
- deepcode
- deepseek_runtime
- llm-harness-agent
- oh-my-deepseek-harness

Remote：

https://github.com/yuanchenglu/<项目名>.git

分支策略：

- 开发分支：develop
- 发布分支：master
- develop 已取消 PR 强制保护，可以直接推送；但 PR 仍是第一优先路径。

执行优先级：

第一优先：走 PR 流程

1. 创建功能/文档分支 → 提 Pull Request → 等待 CI 通过 → 合入 develop。
2. 按各项目 docs/ 目录下的计划文档执行任务。
3. PR 标题和描述必须清楚说明 Work ID、变更、原因、风险、验证和 exclusions。
4. 能走 PR 就走 PR；不得因为 develop 可直推而默认绕过 PR。

第二优先：异常处理与直推

如果 PR 流程持续出问题，例如 CI 环境不可用、测试依赖无法安装、规则冲突或平台故障：

1. 先分析原因：定位根因，确认是代码问题、配置问题还是环境问题。
2. 尝试修复：如果是代码问题，例如缺少文件、配置错误或测试缺陷，直接修复并继续 PR。
3. 解决不了才直推 develop：只有问题在当前环境确实无法解决时，才允许直接推送 develop，避免流程永久阻塞。
4. 不得直推 master。
5. 不得用直推逃避代码缺陷、安全边界、Required CI 或 Gate 条款。

直推 develop 的纪律

1. Commit 信息格式必须包含「问题原因」和「技术债务」：

<type>(<scope>): <变更说明>

## 问题原因
[写明为什么 PR 流程无法通过，真实根因是什么]

## 技术债务
- [列出本次遗留的未解决问题、待办事项]

示例：

feat(auth): add login ticket validation

## 问题原因
CI 环境的 Playwright 依赖版本与本地不一致，E2E 测试在 CI 上无法运行。已手动验证本地通过。

## 技术债务
- Playwright 版本锁定需要统一管理
- E2E 测试在 CI 上需要单独排查

2. 技术债务记录二选一：

方式 A：记录在 Commit 信息中（推荐）

- 在 Commit 的「技术债务」段落使用短横线列表。
- 后续执行者必须根据 Commit 信息判断并处理。

方式 B：记录在项目文档中

- deepseekagent → docs/TECH_DEBT.md 或 docs/BUG_LIST.md
- deepcode → docs/BUG_LIST.md
- deepseek_runtime → docs/TECH_DEBT.md
- oh-my-deepseek-harness → docs/TECH_DEBT.md
- llm-harness-agent → TECH_DEBT.md（根目录）

每条格式：

[日期] 描述 | 遗留原因 | 状态

核心原则：

- 能走 PR 就走 PR，直推是兜底方案，不是默认方案。
- 直推必须有交代：Commit 信息必须说清楚为什么直推、留下了什么。
- 技术债务不怕有，怕没人知道；记录下来是解决的第一步。

六、会话结束前的远程持久化要求

1. 不允许把唯一代码或文档只留在临时容器中。
2. 会话结束前必须检查 git status、当前分支、Commit 和 remote 状态（若存在本地 checkout）。
3. 所有属于本任务的变更必须 Commit 并推送到 GitHub。
4. 能合入 develop 就按 PR + CI + Squash Merge 完成。
5. 若暂时不能合入 develop，至少推送到专用远程分支，并在最终报告中给出：branch、commit SHA、PR、CI 状态、未合入原因和技术债务。
6. 不得承诺稍后上传；必须在当前会话完成远程持久化。
7. 新会话只相信远程，不相信旧容器中可能存在的文件。

七、严格边界

- 不合入 master，不创建 Tag、GitHub Release 或 PyPI publication。
- Gate 评估不得修改 Runtime、Tool/API/DB/domain 实现；发现缺陷应建立或引用明确 Issue。
- 不把 fake Hermes CLI 或 package-level CI 描述为真实 Hermes integration E2E。
- 不把 QA-ART-001 绿色 CI描述为 reproducible-build、G1 或 Public Beta PASS。
- 保持目标 10 Tools、当前 Runtime 9 Tools；不得创建 placeholder memory_store。
- 不读取或修改真实用户 HOME、DB、Memory、Secret。
- 不向无法证明归属的 PID 发送信号。
- 若 Gate 条款证据不足，结论必须是 BLOCKED，不得猜测 PASS。
- 不并行启动 CTX-001、SES-001 或其他 G1 后继任务。

八、最终报告必须包含

1. 启动时核对的最新 develop Head；
2. QA-ART-001 与 post-merge 收口的最终状态；
3. M1 8/8 的闭环清单；
4. G1 每条标准、证据和判定；
5. G1 最终结论与 exclusions；
6. 修改文件、分支、Commit、PR 和 CI；
7. develop 新基线；
8. 下一个 Work ID 是否合法解锁；
9. CTX-001/SES-001 是否仍被 Gate 阻塞；
10. master、Tag、Release、PyPI 状态；
11. 所有变更是否已经远程持久化，是否存在未推送文件或技术债务。
```
