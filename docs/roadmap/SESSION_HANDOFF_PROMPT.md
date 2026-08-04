# 新会话交接提示词

```text
你继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格、串行、持续完成 Open-source Beta -> Stable 全计划，直到 v3.0.0 发布。
用户明确要求：本次会话一次性全部完成剩余所有任务（MEM-001 起，直到 v3.0.0）。
除真实 Owner 决策、外部平台审核或真实日历时间 Gate（M5 Beta 至少 14 天、M6 SOAK 至少 14 天）外，
不等待"继续"。每完成一个 Work ID 或 Gate，重新读取远程 develop 并启动下一个唯一合法任务。

════════════════════════════════════════════════
一、远程唯一事实源（启动时必须核验）
════════════════════════════════════════════════
启动后核验 develop、master、全部远程分支、开放 PR、canonical Issues、Review Threads、CI、Artifacts、Tags、Releases 与 Rulesets，并完整阅读：

- docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md（v2.3.15 或更新）
- docs/roadmap/EXECUTION_STATUS.md
- docs/roadmap/SESSION_HANDOFF_PROMPT.md
- docs/roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md（全部 48 Work ID、授权路径、硬依赖、88 FR、17 CR、100 Test IDs、G0-G5、发布协议）
- docs/testing/TEST_PLAN.md
- docs/testing/evidence/GATE-G0.md / GATE-G1.md / GATE-G2.md
- docs/testing/evidence/CTX-001.md ~ CTX-004.md / SES-001.md / PRIV-001.md / CON-001.md
- docs/traceability/RELEASE_TRACEABILITY.md（每个 Work ID 的 Issue 编号、依赖、验收、凭证）
- docs/product/PRD.md（FR-POLICY / FR-MEMORY / FR-PLAN / FR-CONTEXT / FR-SEC / FR-OBS 等全部契约）
- docs/architecture/TECHNICAL_ARCHITECTURE.md
- docs/compatibility/HERMES_MATRIX.md

任何交接快照与 GitHub 事实冲突时，以远程事实为准并同步修正文档。

════════════════════════════════════════════════
二、当前事实快照（2026-08-04）
════════════════════════════════════════════════
- 当前 develop 基线：master（COMPAT-001 merge 后更新）
- master：398701c5cf6495180a7a7566f09921cf126a054a（与 develop diverged，不提前合并）
- 固定 Work ID：48
- Complete：37/48（77.1%）
- Not started / dependency blocked：11/48
- M0：Complete / G0：PASS
- M1：8/8 Complete / G1：PASS
- M2：Complete（CTX-001/002/003/004 + SES-001 + PRIV-001）/ G2：PASS
- M3：Complete（10/10）
- M4：DOC-001 + DOC-002 + QA-001 + QA-002 + COMPAT-001 Complete（PR #110/#112/#113/#116/#118）
- 产品成熟度：Experimental Preview
- 下一唯一合法任务：SEC-001（#47）
- XFAIL：**0（全清）**
- master、Tag、GitHub Release、PyPI 均未进入发布阶段
- PyPI 按 REL-005 保持禁用

════════════════════════════════════════════════
三、剩余任务全清单（11 个 Work ID + 4 个 Gate）
════════════════════════════════════════════════
M3（Contract & Data Integrity，退出 G3）：
- MEM-001 #33：✅ Complete（PR #101）— memory_store/Tag/Query、content hash、source identity、mtime、import batch、λ 连续边界
- MEM-002 #34：✅ Complete（PR #102）— 默认关闭 startup import、固定 CLI/API delete、dry run、迁移报告；Delete 缺 --confirm 拒绝；不增加公共 Tool
- PLAN-001 #35：✅ Complete（PR #103）— 自依赖/缺失依赖/跨 Plan/循环、更新后校验、Cascade 影响集合
- PLAN-002 #36：✅ Complete（PR #104）— 状态机、创建/更新事务、短任务重复步骤修复
- PLAN-003 #37：✅ Complete（PR #105）— 用 plan_status 承担公共 Query、固定 CLI/API Delete/Archive、禁止跨 Plan 删除
- CP-001 #38：✅ Complete（PR #106）— Plan/Completed ID 归属、并发编号、Review Rule Version
- AUD-001 #39：✅ Complete（PR #107）— JSONL 事件源 + Markdown 派生报告（XF-AUDIT-001 转 Pass）
- OPS-001 #40：✅ Complete（PR #108）— 手工 audit 命令、Cron 降级为不自动安装示例
- INTENT-001 #41：✅ Complete（PR #109）— 修复低置信阈值、否定语义、用户显式优先（CON-001 后可并行）

M4（开源可用性、兼容性、RC，退出 G3）：
- DOC-001 #42：✅ Complete（PR #110）— 能力五级状态分级 + evidence-backed README（CR-P2-001/005 收敛）
- DOC-002 #43：✅ Complete（PR #112）— 安装/升级/Doctor/卸载/隐私/Troubleshooting/Known Limitations
- QA-001 #44：✅ Complete（PR #113）— test-fast / test-integration / test-release 三条通道
- QA-002 #45：✅ Complete（PR #116）— Ruff、类型、ShellCheck、Coverage、依赖与 Secret 扫描
- COMPAT-001 #46：✅ Complete（PR #118）— Hermes 注册探针 + 支持矩阵
- SEC-001 #47：SECURITY、第三方许可证、SBOM、发布权限最小化
- MIG-001 #48：从审查基线到 Beta 的 Config/DB/JSONL Migration、拒绝降级、失败回滚（TC-MIG-001-006）
- SEC-002 #49：Local API、文件权限、输入限制、Prompt Injection 边界、破坏性操作保护
- REL-006 #50：Build/Publish/Rollback 自动化、Release Checklist

G3 评估：确认 M2+M3+M4 evidence 齐备、RC 可重复构建、支持矩阵一致。

M5（Public Beta 验证，至少 14 天日历；退出 G4）：
- BETA-001 #51：发布 v3.0.0-beta.1 + 不可变制品（Tag、SHA256、SBOM、provenance、Release Notes）
- BETA-002 #52：按计划第 9 节招募/记录/计算外部验证指标（Wilson 区间可复算）
- BETA-003 #53：逐项分诊 Beta 失败、创建独立修复 Issue、P0 立即暂停
- REL-007 #54：演练发布撤回、用户回滚、诊断通知

M6（Stable 候选；退出 G5）：
- STABLE-001 #55：关闭所有 P1、清理所有 Beta Waiver（P0=0、P1=0）
- SOAK-001 #56：以最终 RC 重新执行 14 天稳定观察（真实日历，不可加速）
- REL-008 #57：G5 通过后发布 v3.0.0（Tag、制品、文档、Changelog 一致）

════════════════════════════════════════════════
四、执行纪律（每 Work ID 必须遵循）
════════════════════════════════════════════════
1. 一次只实施一个 Work ID 或评估一个 Gate；
2. 最新 develop -> 专用分支 -> Draft PR -> TDD Red -> 最小实现 -> Required CI -> Code Review（unresolved threads 0）-> expected-Head Squash Merge；
3. 禁止 skip、弱化断言、删除测试、隐藏 XFAIL/XPASS；
4. 每个 Work ID 建立 docs/testing/evidence/<WORK-ID>.md；
5. 每个有意义批次立即 push；
6. 每完成一个 Work ID 自动更新 Plan(v2.3.x)/Status/Traceability/Handoff 并推进下一个；
7. 上下文腐烂或工具循环时，先 commit、push、更新 Evidence/Status/Handoff 和 Issue，再交接新会话；不得留下仅存在于临时容器的代码。

════════════════════════════════════════════════
五、固定支持与发布边界（不可突破）
════════════════════════════════════════════════
- Hermes 候选：v0.19.0 / Git tag v2026.7.20；
- Python 3.10：package/core/artifact-only；完整 Hermes v0.19.0 组合不支持 Python 3.10；
- Python 3.11-3.12：完整 Hermes 候选支持范围；
- real Hermes E2E 属于 COMPAT-001 / M4 / G3；
- reproducibility、SBOM、provenance 属于 REL-006；
- Runtime 当前 9 real Tools，目标 10；memory_store 由 MEM-001 实现后才注册；
- 不提前合入 master，不提前 Tag/Release，不发布 PyPI；
- 不访问真实 HOME、DB、Memory、Secret；测试用临时 SQLite + 虚拟机 macOS；
- 不弱化 PID、process identity、exact argv、symlink、traversal、rollback 或 destructive-operation 防线；
- M5/M6 的 14 天观察期为真实日历，不可用工程手段加速。

持续目标：MEM-001 -> ... -> M3 完成 -> M4/G3 -> exact-master RC -> v3.0.0-beta.1 -> M5 Beta/G4 -> M6 Stable/G5 -> v3.0.0。
```