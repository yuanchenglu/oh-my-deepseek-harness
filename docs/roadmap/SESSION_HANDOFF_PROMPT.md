# 新会话交接提示词

将下面完整提示词复制到新会话。新会话不得依赖旧容器、旧工作区或未提交文件，只以 GitHub 远程状态为准。

```text
你现在继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格继续开源发布计划。先核对并完整收口 INS-002；只有 PR #70 已合并且 Issue #23 已关闭时，下一项唯一允许启动的 Work ID 才是 `INS-003` #24。不得并行启动 QA-ART-001 或其他后继任务。

一、必须先读取和核对的远程信息

1. docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md（规范版本 v2.3.4）
2. docs/roadmap/EXECUTION_STATUS.md
3. docs/roadmap/SESSION_HANDOFF_PROMPT.md
4. docs/testing/evidence/INS-002.md
5. docs/traceability/RELEASE_TRACEABILITY.md
6. INS-002 Canonical Issue：#23
7. INS-002 Delivery PR：#70
8. INS-002 代码验收 Head：ef4363cd8972c0e9bba64ae91a84a6efa8806e2e
9. INS-002 Required CI：Run #134 / ID 30335296725
10. INS-003 Canonical Issue：#24
11. 当前 develop Head：必须通过 GitHub 重新读取，不得根据提示词猜测。

远程事实优先：

- 若 PR #70 尚未合并或 Issue #23 尚未关闭，只允许继续 INS-002 收口，不得启动 INS-003；
- 若 #70 已 protected Squash Merge 且 #23 Closed / completed，才允许从最新 develop 启动 INS-003。

二、INS-002 验收状态

固定总分母：48 个 Work ID。INS-002 合并后：

- Complete：14/48（29.2%）
- In progress：0/48
- Not started / dependency blocked：34/48
- M0 已完成，G0 PASS
- M1：6/8 Complete、0/8 In progress、1/8 Open eligible、1/8 Blocked
- G1 尚未评估
- 产品成熟度仍为 Experimental Preview

INS-002 代码验收：

- Run #134 / ID 30335296725
- Python 3.10、3.11、3.12 全绿
- 每版本 215 tests、0 failures、0 errors、9 个 strict XFAIL

已验证：

- human 与单 JSON object 共用一个 DoctorReport；
- exits 1/3/4/5 对应 generic/missing dependency/unmanaged port/unsupported；
- Python/Hermes/Plugin/Context/config/Server/DB/Provider/permissions；
- Python 3.10 + Hermes 明确拒绝为完整支持；
- unmanaged port 不启动、不停止、不发信号；
- 空 HOME 无写入，Doctor 不调用 pip、不自动修复；
- Secret 与 managed absolute path 不输出；
- Linux zombie 视为 exited，不弱化 foreign/PID-reuse ownership。

三、INS-003 固定目标

Canonical Issue：#24。

目标：实现 deployment/config/data upgrade、ordinary uninstall、confirmed purge 与 interrupted-install recovery，覆盖 `FR-INSTALL-004–005` 和 `TC-INSTALL-006–008/010`。

必须满足：

1. 同版本 upgrade 幂等；版本变化时先备份 managed deployment/config/DB，再执行事务；
2. upgrade 失败可恢复 prior config/DB/deployment；不完整 rollback 为 P0，并输出手工恢复路径；
3. ordinary uninstall 只移除 managed adapters/runtime deployment，保留 Python distribution、用户数据、DB、Memory 和备份；
4. CLI **绝不调用 pip**，只打印精确命令：`python -m pip uninstall oh-my-deepseek-harness`；
5. purge 必须显式确认，默认拒绝；
6. purge 只允许删除 canonical product root 内 owned paths，拒绝 symlink、path traversal、root/home/`.hermes` 父目录；
7. interrupted install/upgrade 可从 transaction marker 和 backup 恢复；
8. 使用临时 HOME/data/DB/port、fixture backups 和 fake secrets；
9. 不实现完整 Beta Migration；该范围归 MIG-001。

四、执行顺序

1. 读取 Issue #24 全文和评论。
2. 读取 PRD、Architecture、Test Plan、Traceability 中 `FR-INSTALL-004–005`、`TC-INSTALL-006–008/010`、destructive-operation security 与 rollback 契约。
3. 从最新 develop 创建专用分支，建议 `feat/ins-003-lifecycle-recovery`，立即建立 Draft PR。
4. 先建立 transaction/backup/path-boundary 模型和失败注入测试，再接 CLI。
5. ordinary uninstall、purge、upgrade 和 recover 必须共用唯一 lifecycle implementation，不在 shell 中维护第二套逻辑。
6. 完成 same-version/upgrade、ordinary uninstall、confirmed purge、interrupted recovery 和 symlink/traversal tests。
7. 运行 Python 3.10、3.11、3.12 Required CI，修复真实根因。
8. 更新 INS-003 Evidence、Traceability、Execution Status、主计划和 PR 描述。
9. 全绿后标记 Ready，protected Squash Merge 到 develop，并关闭 Issue #24。
10. 只有 INS-003 完整关闭后，才允许启动 QA-ART-001 #25。

五、严格约束

- develop 为开发分支；master 为发布分支。
- 功能分支 → PR → Required CI → Squash Merge develop；不得直推 develop。
- 不合入 master，不创建 Tag、GitHub Release 或 PyPI publication。
- CLI 不得调用 pip，不得卸载 Python distribution。
- 不删除用户 data、DB、Memory、Secret 或非 owned 文件。
- purge 必须 confirmed 且 path-boundary fail-closed。
- 不实现 MIG-001 的完整 Beta migration。
- 不修改 Tool/API/DB/domain contract。
- 保持 10 个目标 Tool、9 个当前 Runtime Tool；不得创建 placeholder memory_store。
- Python 3.10 仅为 package/core CI；完整 Hermes v0.19.0 支持为 Python 3.11–3.12。
- 不向无法证明归属的 PID 发送任何信号。
- 不把绿色 CI 描述为 G1/Public Beta Ready。

最终报告：

1. INS-003 审查发现；
2. 修改文件和 Commit；
3. PR 状态；
4. Python 3.10、3.11、3.12 CI；
5. upgrade/uninstall/purge/recovery 与 path-boundary 证据；
6. INS-003 是否真正完成；
7. develop 新基线；
8. QA-ART-001 是否已合法解锁。
```
