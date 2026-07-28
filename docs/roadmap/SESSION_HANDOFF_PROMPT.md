# 新会话交接提示词

将下面完整提示词复制到新会话。新会话不得依赖旧容器、旧工作区或未提交文件，只以 GitHub 远程状态为准。

```text
你现在继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格继续开源发布计划。先核对并完整收口 INS-001；只有 PR #68 已合并且 Issue #22 已关闭时，下一项唯一允许启动的 Work ID 才是 `INS-002` #23。不得并行启动 INS-003 或其他后继任务。

一、必须先读取和核对的远程信息

1. docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md（规范版本 v2.3.4）
2. docs/roadmap/EXECUTION_STATUS.md
3. docs/roadmap/SESSION_HANDOFF_PROMPT.md
4. docs/testing/evidence/INS-001.md
5. docs/traceability/RELEASE_TRACEABILITY.md
6. INS-001 Canonical Issue：#22
7. INS-001 Delivery PR：#68
8. INS-001 代码验收 Head：48f547f9b3c3fae27fc5672c24f0ff5380c65583
9. INS-001 Required CI：Run #121 / ID 30333369939
10. INS-002 Canonical Issue：#23
11. 当前 develop Head：必须通过 GitHub 重新读取，不得根据提示词猜测。

先核对分支、Commit、PR、Issue、CI 和文件内容。远程事实优先：

- 若 PR #68 尚未合并或 Issue #22 尚未关闭，只允许继续 INS-001 收口，不得启动 INS-002；
- 若 #68 已 protected Squash Merge 且 #22 Closed / completed，才允许从最新 develop 启动 INS-002。

二、INS-001 验收状态

固定总分母：48 个 Work ID。INS-001 合并后：

- Complete：13/48（27.1%）
- In progress：0/48
- Not started / dependency blocked：35/48
- M0 已完成，G0 PASS
- M1：5/8 Complete、0/8 In progress、1/8 Open eligible、2/8 Blocked
- G1 尚未评估
- 产品成熟度仍为 Experimental Preview

INS-001 代码验收：

- Run #121 / ID 30333369939
- Python 3.10、3.11、3.12 全绿
- 每版本 206 tests、0 failures、0 errors、9 个 strict XFAIL
- `XF-INSTALL-001` 已关闭

已验证：

- 空 HOME dry-run 无持久变化；
- 外部 wheel clean install；
- packaged Plugin/Context adapters 与私有数据路径；
- Supervisor Server health/ready/status；
- 重复安装同版本复用同 PID、managed files 不变；
- 无重复 config/state/backup/import；
- 用户冲突/symlink 内容保留并 fail-closed；
- rollback 不完整时保留 ownership/deployment state，退出码 6；
- CLI 不调用 pip；shell 只路由 canonical CLI。

三、INS-002 固定目标

Canonical Issue：#23。

目标：实现 `deepseek-harness doctor [--json]` 的人类和单 JSON object 输出，覆盖 `FR-INSTALL-006`、`FR-OBS-003/005` 与 `TC-INSTALL-004/005/009`。

必须检查并区分：

1. Python 版本与 package/core 支持；
2. Hermes 可执行文件、版本 `0.19.0` 和 Python 组合；
3. Plugin/Context adapters、manifest 与 import；
4. Server state、PID ownership、port、`/health`、`/ready`、`/version`；
5. DB 可创建/访问、数据根与权限；
6. 缺依赖和端口冲突的可执行修复提示；
7. Python 3.10 的完整 Hermes 组合必须明确拒绝，不能描述为支持；
8. human 输出与 `--json` 必须由同一结构化诊断结果渲染；
9. Doctor 不得修改状态、启动/停止 Server、调用 pip 或写真实 HOME。

四、执行顺序

1. 读取 Issue #23 全文和评论。
2. 读取 PRD、Architecture、Test Plan、Traceability 中 Doctor 与 `TC-INSTALL-004/005/009` 契约。
3. 从最新 develop 创建专用分支，建议 `feat/ins-002-doctor`，立即建立 Draft PR。
4. 先建立结构化 Check/Report 模型和无副作用测试，再接 CLI。
5. 使用临时 HOME/data/DB/port、fake executable/version fixture；不依赖真实 Hermes 或用户环境。
6. 完成 human/JSON parity、缺依赖、端口冲突、Python/Hermes 支持矩阵测试。
7. 运行 Python 3.10、3.11、3.12 Required CI，修复真实根因。
8. 更新 INS-002 Evidence、Traceability、Execution Status、主计划和 PR 描述。
9. 全绿后标记 Ready，protected Squash Merge 到 develop，并关闭 Issue #23。
10. 只有 INS-002 完整关闭后，才允许启动 INS-003 #24。

五、严格约束

- develop 为开发分支；master 为发布分支。
- 功能分支 → PR → Required CI → Squash Merge develop；不得直推 develop。
- 不合入 master，不创建 Tag、GitHub Release 或 PyPI publication。
- INS-002 不实现 Upgrade、Uninstall、Purge 或 Migration。
- Doctor 必须只读；不得自动修复、启动 Server、修改配置或调用 pip。
- 不修改 Tool/API/DB/domain contract。
- 保持 10 个目标 Tool、9 个当前 Runtime Tool；不得创建 placeholder memory_store。
- Python 3.10 仅为 package/core CI；完整 Hermes v0.19.0 支持为 Python 3.11–3.12。
- 不使用真实用户 HOME、DB、Memory 或 Secret。
- 不向无法证明归属的 PID 发送任何信号。
- 不把绿色 CI 描述为 G1/Public Beta Ready。

最终报告：

1. INS-002 审查发现；
2. 修改文件和 Commit；
3. PR 状态；
4. Python 3.10、3.11、3.12 CI；
5. Doctor human/JSON 与失败矩阵证据；
6. INS-002 是否真正完成；
7. develop 新基线；
8. INS-003 是否已合法解锁。
```
