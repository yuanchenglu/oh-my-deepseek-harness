# 新会话交接提示词

```text
你继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格、串行、持续完成 Open-source Beta → Stable 全计划。除真实 Owner 外部门禁外，不等待“继续”。每完成一个 Work ID 或 Gate，重新读取最新远程 develop，并启动下一个唯一合法任务。

一、远程唯一事实源

启动后读取最新 develop、master、开放 PR、开放 canonical Issues、最近 CI，以及：

- docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md（v2.3.9 或更新）；
- docs/roadmap/EXECUTION_STATUS.md；
- docs/roadmap/SESSION_HANDOFF_PROMPT.md；
- docs/roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md；
- docs/testing/TEST_PLAN.md；
- docs/testing/evidence/GATE-G1.md；
- docs/testing/evidence/QA-ART-001.md；
- docs/testing/evidence/CTX-001.md；
- docs/traceability/RELEASE_TRACEABILITY.md；
- docs/compatibility/HERMES_MATRIX.md。

交接快照与 GitHub 事实冲突时，以远程事实为准并同步修正文档。

二、当前事实快照

- develop：4026fea226c16647c45d710993c9b4c1683e094e
- master：398701c5cf6495180a7a7566f09921cf126a054a
- 固定 Work ID：48
- Complete：17/48（35.4%）
- In progress：0/48
- Not started / dependency blocked：31/48
- M0：Complete
- G0：PASS
- M1：8/8 Complete
- G1：PASS
- CTX-001：Complete
- 产品成熟度：Experimental Preview
- master、Tag、GitHub Release、PyPI 尚未进入当前发布阶段
- PyPI 按 REL-005 保持禁用

三、CTX-001 完成事实

- Issue #26：Closed / completed
- PR #81：Merged
- TDD red：Run #197 / ID 30384981106
- Code acceptance：Run #201 / ID 30385826868
- Final Head：bae32c861fc403896e0c1630b91457d1622e2737
- Final CI：Run #202 / ID 30386119025
- Squash：4026fea226c16647c45d710993c9b4c1683e094e
- Python 3.10/3.11/3.12：每版本 234 tests、0 failures、0 errors、8 strict XFAIL
- `TC-CTX-003`：普通 PASS
- `CR-P0-002`、`XF-CTX-001`：Closed
- 精确完整 Merge 双副本删除；普通重复消息与不完整疑似序列不被误删

四、当前唯一合法任务：CTX-002 #27

完成 docs-only CTX-001 post-merge closure 后：

1. 读取 Issue #27 全文与评论；
2. 核对依赖、授权路径、CR-P0-003、TC-CTX-004–006、XF-CTX-002；
3. 从最新 develop 创建 fix/ctx-002-summary-failure-preservation；
4. 评论执行开始、基线、范围与 exclusions；
5. 将 summary-failure strict XFAIL 转为普通失败回归；
6. 创建 Draft PR；
7. 最小修复摘要 API 失败时压缩区原消息被占位文本替换的问题；
8. 保证 fallback 非破坏性、消息顺序和内容保持；
9. 不提前实施 CTX-003/004、SES-001、PRIV-001；
10. 创建 docs/testing/evidence/CTX-002.md；
11. 同一最终 Head Required CI 全绿后 expected-Head Squash Merge；
12. 关闭 #27 并自动进入 CTX-003。

五、M2 固定串行顺序

CTX-002 → CTX-003 → CTX-004 → SES-001 → PRIV-001 → G2

SES-001 的硬依赖已满足，但禁止并行启动。

六、固定边界

- Hermes 候选：v0.19.0 / Git tag v2026.7.20；
- Python 3.10 仅 package/core/artifact lifecycle，完整 Hermes 候选矩阵为 3.11–3.12；
- real Hermes E2E 属于 COMPAT-001 / M4 / G3；
- reproducibility、SBOM、provenance 属于 REL-006；
- Runtime 当前 9 Tools，目标 10；不得添加 placeholder memory_store；
- 当前 8 strict XFAIL owners：CTX-002、CTX-003、SES-001、AUD-001、CON-001×3、MEM-002；
- 不合入 master，不创建 Tag/Release，不发布 PyPI；
- 不访问真实 HOME、DB、Memory、Secret；
- 不弱化 PID、symlink、traversal、rollback 或 destructive-operation 防线。

七、执行纪律

- 一次只实施一个 Work ID 或评估一个 Gate；
- 专用分支 → Draft PR → Required CI → Ready → expected-Head Squash Merge develop；
- 先失败测试，再最小正确实现；
- 禁止 skip、弱化断言、删除测试、隐藏 XFAIL/XPASS；
- 每个 Work ID 建立 docs/testing/evidence/<WORK-ID>.md；
- 每个有意义批次立即 push；
- 合并后自动读取最新 develop 并继续下一个唯一任务。

持续目标：CTX-002 → M2/G2 → M3 → M4/G3 → master RC → v3.0.0-beta.1 → Beta feedback/G4 → Stable prep/soak/G5 → v3.0.0。
```
