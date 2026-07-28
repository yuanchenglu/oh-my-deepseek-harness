# 新会话交接提示词

将下面完整提示词复制到新会话。新会话不得依赖旧容器、旧工作区或未提交文件，只以 GitHub 远程状态为准。

```text
你现在继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格继续开源发布计划，先完整收口当前唯一 Work ID `RUN-002`，不要并行启动后继任务。

一、必须先读取和核对的远程信息

1. 主计划：
   - docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md
   - 当前版本应为 v2.3.4
2. 执行状态：
   - docs/roadmap/EXECUTION_STATUS.md
3. 当前交接文件：
   - docs/roadmap/SESSION_HANDOFF_PROMPT.md
4. RUN-002 Evidence：
   - docs/testing/evidence/RUN-002.md
5. Canonical Issue：#21
6. Draft PR：#65
7. 当前工作分支：feat/run-002-supervisor
8. 已合并 develop 基线：
   - 31366ceb1cb1ff375496bed2cdaf504ac11763ae
9. 远程 WIP 保存 Commit：
   - 5e0e9eaf11da28a0b181981b8c4ebd30b26d199e

先通过 GitHub 实际核对分支、Commit、PR、CI 和文件内容。不要根据提示词直接假设远程状态没有变化；远程事实优先。

二、已经完成的整体进度

固定总分母：48 个 Work ID。

- Complete：11/48（22.9%）
- In progress：1/48（RUN-002）
- Not started / blocked：36/48
- M0 已完成
- G0 已 PASS
- M1：3/8 Complete、1/8 In progress、4/8 Blocked
- G1 尚未评估
- 产品成熟度仍是 Experimental Preview，不得声称 Public Beta Ready

已完成并合入 develop：

- REL-000：PR #4 / e18db7e
- REL-001：PR #6 / a97dfe4
- REL-002：PR #8/#9 / e7e1414e / 61642f69
- REL-004：PR #11 / 7d52de9f
- GOV-001：PR #14 / a0083ce1
- REL-003：PR #58 / fd5c212f
- REL-005：PR #59 / 49ad479f
- COMPAT-000：PR #60 / c7f6212a
- G0：PR #61 / ee516c9b
- PKG-001：PR #62 / 2098dffc
- PKG-002：PR #63 / ae277d1d
- RUN-001：PR #64 / 31366ceb

RUN-001 最终验证：Python 3.10/3.11/3.12 全绿；189 tests、0 failures、0 errors、10 个既有 strict XFAIL。

三、RUN-002 当前 WIP 内容

Draft PR #65 当前远程保存了：

- src/harness_server/runtime.py
  - RuntimePaths / RuntimeState
  - 原子 state 写入
  - 跨进程 lock
  - PID + random instance ID ownership
  - 内部 child process 入口
- src/harness_server/supervisor.py
  - start/status/stop/restart
  - port、health、ready、version 验证
  - foreign PID 拒绝
  - user-accessible combined stdout/stderr log
- src/deepseek_harness/cli.py
  - deepseek-harness server start/status/stop/restart
  - human/JSON 输出和退出码
- src/deepseek_harness/tools.py
  - Hermes Tool 自动启动统一使用同一 Supervisor
- pyproject.toml
  - deepseek-harness console script
- tests/test_server_process.py
  - 并发 start 单 PID
  - status
  - restart 新 instance
  - stop 幂等
  - 权限和日志
  - foreign PID/no-signal
  - port conflict

注意：这是 WIP 保存点，不代表代码正确，也不代表 CI 已通过，更不允许直接合并。

四、你必须按顺序执行

1. 检查 Draft PR #65 当前 Head、Changed Files、Diff 和所有 CI。
2. 对 RUN-002 做严格 Code Review，重点检查：
   - 是否可能误杀 unrelated PID；
   - PID reuse 后是否仍可能误判 ownership；
   - instance ID 是否真实出现在 child command line；
   - start/status/stop/restart 是否都持有正确锁；
   - 两个独立进程同时 start 是否只产生一个 Server；
   - stale/corrupt/foreign state 是否安全处理；
   - port 已被 unmanaged process 占用时是否明确失败；
   - stop 是否幂等；
   - SIGTERM 超时后 SIGKILL 前是否再次验证 ownership；
   - 日志/state/lock/data 目录权限是否符合 0700/0600；
   - 测试是否只使用临时 HOME、DB、port、data root；
   - Windows 未支持部分是否被明确 skip，而非伪装通过。
3. 运行或读取 Python 3.10、3.11、3.12 Required CI。
4. CI 失败时读取 JUnit/Actions 日志，修复真实根因；禁止删除或弱化并发、foreign PID、权限、日志和失败注入测试。
5. 补齐并更新：
   - docs/testing/evidence/RUN-002.md
   - docs/traceability/RELEASE_TRACEABILITY.md 中 RUN-002 行
   - docs/roadmap/EXECUTION_STATUS.md
   - PR #65 的最终说明
6. 所有 Required Checks 成功后，将 Draft PR 标记为 Ready，再按 Ruleset Squash Merge 到 develop。
7. 合并后：
   - 记录 Squash Commit；
   - 更新 Issue #21 完成证据并关闭；
   - 验证 develop Head 和 CI；
   - 更新计划进展。
8. 只有 RUN-002 完整合并并关闭后，才允许启动 INS-001 #22。

五、严格约束

- 开发分支 develop；发布分支 master。
- 第一优先走功能分支 → PR → CI → Squash Merge develop。
- 不允许为了省事直推 develop 绕过 Ruleset。
- 不合入 master。
- 不创建 Tag、GitHub Release 或 PyPI publication。
- 不新增产品功能，不做 feature creep。
- 不修改 Tool/API/DB/domain contract，除非 RUN-002 的真实阻断要求且先在 Issue/PR 记录范围变更。
- 10 个目标 Tool、9 个当前 Runtime Tool 保持不变；不得创建 placeholder memory_store。
- Python 3.10 仅为 package/core CI；真实 Hermes v0.19.0 完整支持为 Python 3.11–3.12。
- 不把静态测试、绿色单测或 WIP PR 描述为 Public Beta Ready。
- 不使用真实用户 HOME、真实 DB、真实 Memory 或 Secret 做测试。
- 不向无法证明归属的 PID 发送任何信号。
- 不要问不必要的确认问题；先从 GitHub 远程证据开始独立完成工作。

最终向我报告：

1. 审查发现；
2. 修改文件和 Commit；
3. PR #65 当前状态；
4. 三版本 CI 结果；
5. RUN-002 是否真正完成；
6. develop 新基线；
7. 下一项是否已合法解锁。
```
