# 新会话交接提示词

将下面完整提示词复制到新会话。新会话不得依赖旧容器、旧工作区或未提交文件，只以 GitHub 远程状态为准。

```text
你现在继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格继续开源发布计划。先核对并完整收口 INS-003；只有 PR #72 已合并且 Issue #24 已关闭时，下一项唯一允许启动的 Work ID 才是 `QA-ART-001` #25。不得并行启动 G1、CTX-001 或其他后继任务。

一、必须先读取和核对的远程信息

1. docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md（规范版本 v2.3.4）
2. docs/roadmap/EXECUTION_STATUS.md
3. docs/roadmap/SESSION_HANDOFF_PROMPT.md
4. docs/testing/evidence/INS-003.md
5. docs/traceability/RELEASE_TRACEABILITY.md
6. INS-003 Canonical Issue：#24
7. INS-003 Delivery PR：#72
8. INS-003 代码验收 Head：e2b82c727a3dedaa1c8cc71de38a54dec3c079b6
9. INS-003 Required CI：Run #149 / ID 30339801279
10. QA-ART-001 Canonical Issue：#25
11. 当前 develop Head：必须通过 GitHub 重新读取，不得根据提示词猜测。

远程事实优先：

- 若 PR #72 尚未合并或 Issue #24 尚未关闭，只允许继续 INS-003 收口，不得启动 QA-ART-001；
- 若 #72 已 protected Squash Merge 且 #24 Closed / completed，才允许从最新 develop 启动 QA-ART-001。

二、INS-003 验收状态

固定总分母：48 个 Work ID。INS-003 合并后：

- Complete：15/48（31.3%）
- In progress：0/48
- Not started / dependency blocked：33/48
- M0 已完成，G0 PASS
- M1：7/8 Complete、0/8 In progress、1/8 Open eligible
- G1 尚未评估
- 产品成熟度仍为 Experimental Preview

INS-003 代码验收：

- Run #149 / ID 30339801279
- Head e2b82c727a3dedaa1c8cc71de38a54dec3c079b6
- Python 3.10、3.11、3.12 全绿
- 每版本 228 tests、0 failures、0 errors、9 个 strict XFAIL

已验证：

- upgrade dry-run 零写入；
- same-version upgrade 幂等、无 backup growth、同 PID；
- version-changing upgrade backup-first；
- 普通失败恢复 deployment/config/DB/events/process；
- interrupted transaction marker + explicit recover + retry；
- ordinary uninstall 保留 distribution 与用户数据；
- CLI 只打印、不执行 `python -m pip uninstall oh-my-deepseek-harness`；
- purge 缺 confirm 返回 2 且零变化；
- confirmed purge 仅删除 canonical owned product root；
- symlink parent/descendant、unknown path、noncanonical root、manifest traversal fail-closed；
- external DB 保留，external DB symlink 在 process change 前拒绝。

三、QA-ART-001 固定目标

Canonical Issue：#25。

目标：从 clean source snapshot 构建最终 wheel，仅安装该 wheel 到源码目录外的临时环境，并执行完整 artifact lifecycle，覆盖 `FR-INSTALL-001–006`、`FR-PLUGIN-001–005`、`FR-QA-005` 与 `CR-P2-004`。

必须证明：

1. clean snapshot 构建 wheel，记录文件名、SHA256、metadata 和 inventory；
2. 临时 venv 只安装最终 wheel，不使用 editable install，不把仓库路径加入 PYTHONPATH；
3. 所有 product imports 的 `__file__` 均位于临时 environment，不位于 source tree；
4. 使用临时 HOME/data/DB/dynamic port/fake secret；
5. 执行 install dry-run、clean install、Doctor、Server health/ready/version；
6. 执行最小 Tool/API smoke，但不改变 10 target / 9 runtime Tool contract；
7. 执行 upgrade dry-run/幂等 upgrade、ordinary uninstall；
8. ordinary uninstall 后 distribution 仍可 import，并输出精确 pip uninstall 命令；
9. 测试脚本显式执行 pip uninstall distribution，仅作用于临时 venv；
10. 可增加 confirmed purge 的独立临时环境验证，但不得触碰真实 HOME；
11. CI 必须上传 artifact/JUnit 和记录 source-external 证据；
12. QA-ART-001 完成后仍需独立 G1 Evidence 判定，不能自动声明 G1 PASS。

四、执行顺序

1. 读取 Issue #25 全文和评论。
2. 读取 `tests/test_package_artifact.py`、`scripts/test_artifact.sh`、`.github/workflows/ci.yml` 及 artifact/lifecycle 契约。
3. 从最新 develop 创建专用分支，建议 `test/qa-art-001-external-lifecycle`，立即建立 Draft PR。
4. 先建立 source-path contamination assertions、wheel inventory/SHA256 与临时环境 fixture。
5. 只在源码外环境执行完整生命周期；不得从工作区导入 product code。
6. 运行 Python 3.10、3.11、3.12 Required CI，修复真实根因。
7. 更新 QA-ART-001 Evidence、Traceability、Execution Status、主计划和 PR 描述。
8. 全绿后标记 Ready，protected Squash Merge 到 develop，并关闭 Issue #25。
9. 完成 post-merge 文档收口后，单独评估 G1；不得把 QA-ART-001 合并等同于 G1 PASS。
10. G1 未形成独立 PASS Evidence 前，不得启动 CTX-001 或其他 G1 后继任务。

五、严格约束

- develop 为开发分支；master 为发布分支。
- 功能分支 → PR → Required CI → Squash Merge develop；不得直推 develop。
- 不合入 master，不创建 Tag、GitHub Release 或 PyPI publication。
- QA-ART-001 不修改 package/runtime/lifecycle 实现；发现实现缺陷时记录到 Issue #25，并仅在明确必要时扩大路径。
- 不使用 editable install、source PYTHONPATH 或当前工作目录导入造成假绿。
- 不使用真实用户 HOME、DB、Memory、Secret 或固定端口。
- pip install/uninstall 只能发生在临时 venv；产品 CLI 仍不得调用 pip。
- 不实现 MIG-001、Context、Session、Tool/API/DB/domain 或 marketing scope。
- 保持 10 个目标 Tool、9 个当前 Runtime Tool；不得创建 placeholder memory_store。
- Python 3.10 仅为 package/core/artifact lifecycle；完整 Hermes v0.19.0 支持为 Python 3.11–3.12。
- 不向无法证明归属的 PID 发送任何信号。
- 不把绿色 CI 描述为 G1/Public Beta Ready。

最终报告：

1. QA-ART-001 审查发现；
2. 修改文件和 Commit；
3. PR 状态；
4. Python 3.10、3.11、3.12 CI；
5. wheel inventory/SHA256/source-external import 与 lifecycle 证据；
6. QA-ART-001 是否真正完成；
7. develop 新基线；
8. G1 是否具备独立评估条件；
9. CTX-001 是否仍被 Gate 阻塞。
```
