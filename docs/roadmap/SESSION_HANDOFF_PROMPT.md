# 新会话交接提示词

将下面完整提示词复制到新会话。新会话不得依赖旧容器、旧工作区或未提交文件，只以 GitHub 远程状态为准。

```text
你现在继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格继续开源发布计划。先核对并完整收口 QA-ART-001；只有 PR #74 已合并、Issue #25 已关闭且 post-merge 文档收口已合并时，才允许执行独立 G1 Gate 评估。G1 未形成明确 PASS Evidence 前，不得启动 CTX-001 #26、SES-001 #30 或其他 G1 后继任务。

一、必须先读取和核对的远程信息

1. docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md（规范版本 v2.3.4）
2. docs/roadmap/EXECUTION_STATUS.md
3. docs/roadmap/SESSION_HANDOFF_PROMPT.md
4. docs/testing/evidence/QA-ART-001.md
5. docs/testing/evidence/INS-001.md
6. docs/testing/evidence/INS-002.md
7. docs/testing/evidence/INS-003.md
8. docs/traceability/RELEASE_TRACEABILITY.md
9. QA-ART-001 Canonical Issue：#25
10. QA-ART-001 Delivery PR：#74
11. QA-ART-001 代码验收 Head：81195f844b681e85ccf2c0a15fc4935b2b396ed6
12. QA-ART-001 Required CI：Run #161 / ID 30342161995
13. 当前 develop Head：必须通过 GitHub 重新读取，不得根据提示词猜测。
14. 主计划与 v2.2 归档中的 G1 Gate 原始判定标准。

远程事实优先：

- 若 PR #74 尚未合并或 Issue #25 尚未关闭，只允许继续 QA-ART-001 收口；
- 若 QA-ART-001 已合并但 post-merge 文档尚未收口，只允许完成该 docs-only 收口；
- 只有上述两项均完成，才允许建立独立 G1 Evidence；
- G1 评估必须根据规范标准判定 PASS、FAIL 或 BLOCKED，不得因 M1 任务数量达到 8/8 自动 PASS。

二、QA-ART-001 验收状态

固定总分母：48 个 Work ID。QA-ART-001 合并后：

- Complete：16/48（33.3%）
- In progress：0/48
- Not started / dependency blocked：32/48
- M0 已完成，G0 PASS
- M1：8/8 Complete
- G1：仅具备独立评估条件，尚未判定
- 产品成熟度仍为 Experimental Preview

QA-ART-001 代码验收：

- Run #161 / ID 30342161995
- Head 81195f844b681e85ccf2c0a15fc4935b2b396ed6
- Python 3.10、3.11、3.12 全绿
- 每版本 230 tests、0 failures、0 errors、9 个 strict XFAIL
- 每版本另有 artifact JUnit 1 test、0 failures、0 errors

已验证：

- clean `git archive HEAD` 构建 wheel；
- fresh non-editable venv 只安装最终 wheel distribution 与声明依赖；
- repository、archived source 不在 product import origin 或 sys.path；
- wheel 39 files，不包含 plugins/mcp/tests tree；
- install dry-run、clean install、Server health/ready/version、memory-tag smoke；
- Python 3.10 Doctor 按预期退出 5；Python 3.11/3.12 Doctor 退出 0；
- same-version upgrade 幂等并复用 PID；
- ordinary uninstall 保留 distribution/config/DB，并打印精确 pip command；
- 显式 pip uninstall 仅由测试脚本在临时 venv 执行；
- fake Secret 不出现在上传文本证据；
- 三个独立 wheel hash 不同，因此本 Work ID 不声明 reproducible-build PASS，最终 reproducibility 属于 REL-006。

三、G1 独立评估目标

G1 不是 Work ID 数量统计。必须从规范计划/归档提取精确 Gate 条款，并至少核对：

1. M1 八个 Work ID 的 Issue、PR、Squash Commit、Evidence 和 Required CI 是否全部闭环；
2. package/import/install/Doctor/Supervisor/upgrade/uninstall/purge/final-wheel artifact lifecycle 是否具备来源明确的证据；
3. `CR-P0-001` 是否已由 M1 证据闭环，是否仍有属于 G1 的开放 P0 blocker；
4. strict XFAIL 是否只剩后续 M2/M3 canonical owners，M1 不得留下未归属 XFAIL；
5. Python 支持分层是否一致：3.10 仅 package/core/artifact，3.11–3.12 才是完整 Hermes 候选组合；
6. QA-ART-001 wheel hash 不同是否属于 G1 blocker，必须按 Gate 原始条款判断，不得擅自把 REL-006 reproducibility 提前到 G1；
7. 真实 Hermes discovery/Hook/Context/Tool E2E 是否属于 G1，必须按主计划和 HERMES_MATRIX 原始依赖判断，不能自行提前或豁免；
8. 是否存在真实用户 HOME/DB/Secret 污染、foreign PID、symlink/traversal 或 destructive-operation 未闭环风险；
9. Gate Evidence 必须列出每条标准、证据、判定和明确 exclusions；
10. G1 PASS 只解锁 M2 的合法入口，不代表 Public Beta、master 或 publication ready。

四、执行顺序

1. 重新读取最新 develop、PR #74、Issue #25 和所有 M1 Evidence。
2. 完成 QA-ART-001 post-merge docs closure（若尚未完成）。
3. 从最新 develop 创建独立 Gate 分支，建议 `docs/gate-g1-evaluation`，建立 Draft PR。
4. 读取 G1 的规范条款，建立逐条 Gate checklist，不得先写结论。
5. 核对所有 M1 PR/Issue/CI/Artifact 与开放 blocker。
6. 创建 `docs/testing/evidence/GATE-G1.md`，结论只能是 PASS、FAIL 或 BLOCKED。
7. 同步 Execution Status、主计划、Traceability 和 guarded handoff。
8. 运行 Python 3.10、3.11、3.12 Required CI。
9. 全绿后合并 Gate PR，并完成 post-merge 事实收口。
10. 只有 G1 明确 PASS 后，才允许按主计划确定下一个唯一 Work ID；不得并行启动多个 M2 任务。

五、严格约束

- develop 为开发分支；master 为发布分支。
- 功能/文档分支 → PR → Required CI → Squash Merge develop；不得直推 develop。
- 不合入 master，不创建 Tag、GitHub Release 或 PyPI publication。
- Gate 评估不得修改 Runtime、Tool/API/DB/domain 实现。
- 不把 fake Hermes CLI 或 package-level CI 描述为真实 Hermes integration E2E。
- 不把 QA-ART-001 的绿色 CI描述为 reproducible-build、G1 或 Public Beta PASS。
- 保持 10 个目标 Tool、9 个当前 Runtime Tool；不得创建 placeholder memory_store。
- 不读取或修改真实用户 HOME、DB、Memory、Secret。
- 不向无法证明归属的 PID 发送信号。
- 若 Gate 条款证据不足，结论必须是 BLOCKED，不得猜测 PASS。

最终报告：

1. QA-ART-001 是否真正完成及最终 Squash Commit；
2. M1 8/8 的闭环清单；
3. G1 每条标准及证据；
4. G1 最终判定与 exclusions；
5. Gate PR、CI 和 develop 新基线；
6. 下一个 Work ID 是否合法解锁；
7. CTX-001/SES-001 是否仍被 Gate 阻塞；
8. master、Tag、Release、PyPI 状态。
```
