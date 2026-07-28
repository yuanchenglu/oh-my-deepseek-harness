# 新会话交接提示词

将下面完整提示词复制到新会话。新会话不得依赖旧容器、旧工作区或未提交文件，只以 GitHub 远程状态为准。

```text
你现在继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格继续开源发布计划。RUN-002 已完整关闭；下一项唯一允许启动的 Work ID 是 `INS-001` #22。不要并行启动 INS-002 或其他后继任务。

一、必须先读取和核对的远程信息

1. docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md
   - 当前规范版本：v2.3.4
2. docs/roadmap/EXECUTION_STATUS.md
3. docs/roadmap/SESSION_HANDOFF_PROMPT.md
4. docs/testing/evidence/RUN-002.md
5. docs/traceability/RELEASE_TRACEABILITY.md
6. RUN-002 Canonical Issue：#21（应为 Closed / completed）
7. RUN-002 Delivery PR：#65（应为 merged）
8. RUN-002 Squash Commit：
   - f1c04697fcb43e1862cf9d5d4c6ddfa465b4c44b
9. RUN-002 post-merge records PR：#66
10. INS-001 Canonical Issue：#22（应为 Open，尚未开始）
11. 当前 develop Head：必须通过 GitHub 重新读取，不得根据提示词猜测。

先核对分支、Commit、PR、Issue、CI 和文件内容。远程事实优先；若 PR #66 尚未合并，只允许先完成该 RUN-002 文档收口，不得启动 INS-001。

二、当前整体状态

固定总分母：48 个 Work ID。

- Complete：12/48（25.0%）
- In progress：0/48
- Not started / dependency blocked：36/48
- M0 已完成
- G0 已 PASS
- M1：4/8 Complete、0/8 In progress、1/8 Open eligible、3/8 Blocked
- G1 尚未评估
- 产品成熟度仍为 Experimental Preview，不得声称 Public Beta Ready

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
- RUN-002：PR #65 / f1c04697

RUN-002 最终 Required CI：

- Final PR head：094c4c56f7d75d96ce6aed17132729b4196ed9d5
- Run #108 / ID 30330735858：Python 3.10、3.11、3.12 全绿
- Run #109 / ID 30330754105：相同 Head 的重复三版本验证全绿
- 每版本：200 tests、0 failures、0 errors、10 个既有 strict XFAIL

三、INS-001 固定目标

Canonical Issue：#22

目标：实现 dry-run、clean install 和 idempotent repeated install。

必须满足：

1. dry-run 不产生任何持久变更；
2. 从已安装 distribution 完成 clean deployment；
3. clean install 后 Plugin、Context、Server 达到 Issue #22 定义的 ready 状态；
4. 重复 install 不产生重复配置、重复进程或重复 import；
5. 只使用临时 HOME、data root、DB、port 和 fake secrets；
6. 保留既有文件和权限，失败时可回滚本次 transaction 创建的内容；
7. 测试并追踪 `FR-INSTALL-001–003`、相关 Plugin/Security 契约和 `TC-INSTALL-001–003`。

四、执行顺序

1. 读取 Issue #22 全文和评论。
2. 读取主计划、PRD、Product/Technical Architecture、Test Plan、Traceability 中 INS-001、Installer、Plugin、Security 的规范。
3. 从最新 `develop` 创建专用功能分支；建议名称 `feat/ins-001-install-lifecycle`。
4. 在写代码前审查当前 installer、CLI、resources、install script 和现有测试，确认 package-installed 与 repository checkout 的边界。
5. 先建立临时 HOME 的 before/after snapshot 和失败回滚测试，再实现最小代码。
6. 完成 `TC-INSTALL-001–003`：dry-run、clean install、idempotent repeated install。
7. 运行 Python 3.10、3.11、3.12 Required CI；Python 3.10 仅为 package/core 与预期拒绝层，不得描述为完整 Hermes 支持。
8. 更新 INS-001 Evidence、Traceability、Execution Status 和 PR 描述。
9. 所有 Required Checks 通过后标记 Ready，按 Ruleset Squash Merge 到 develop。
10. 合并并关闭 Issue #22 后，才允许启动 INS-002 #23。

五、严格约束

- 开发分支 develop；发布分支 master。
- 功能分支 → PR → Required CI → Squash Merge develop；不得直推 develop 绕过 Ruleset。
- 不合入 master。
- 不创建 Tag、GitHub Release 或 PyPI publication。
- 不新增产品功能，不做 feature creep。
- INS-001 不包含 Doctor、Upgrade、Uninstall、pip self-management 或 package layout 重构。
- 不修改 Tool/API/DB/domain contract，除非真实阻断且先在 Issue/PR 记录范围变化。
- 10 个目标 Tool、9 个当前 Runtime Tool 保持不变；不得创建 placeholder memory_store。
- Python 3.10 仅为 package/core CI；完整 Hermes v0.19.0 支持为 Python 3.11–3.12。
- 不把绿色单测、静态检查或 WIP PR 描述为 G1/Public Beta Ready。
- 不使用真实用户 HOME、DB、Memory 或 Secret。
- 不向无法证明归属的 PID 发送任何信号。
- 不要问不必要的确认问题；先从 GitHub 远程证据开始独立完成工作。

最终报告：

1. INS-001 审查发现；
2. 修改文件和 Commit；
3. PR 状态；
4. Python 3.10、3.11、3.12 CI；
5. dry-run / clean install / idempotent install 证据；
6. INS-001 是否真正完成；
7. develop 新基线；
8. INS-002 是否已合法解锁。
```
