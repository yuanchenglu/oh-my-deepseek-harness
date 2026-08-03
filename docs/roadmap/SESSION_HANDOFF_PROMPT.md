# 新会话交接提示词

```text
你继续负责 GitHub 仓库：yuanchenglu/oh-my-deepseek-harness。

目标：严格、串行、持续完成 Open-source Beta -> Stable 全计划。

一、当前事实快照

- 当前 develop 基线：待 PRIV-001 squash merge 后确定
- master：398701c5cf6495180a7a7566f09921cf126a054a
- develop 与 master 仍 diverged
- Complete：22/48（45.8%）
- M0：Complete / G0：PASS
- M1：8/8 Complete / G1：PASS
- M2：CTX-001/002/003/004 + SES-001 + PRIV-001 全部 Complete
- 下一唯一合法任务：G2 Gate 评估
- 产品成熟度：Experimental Preview
- 5 strict XFAIL owners：AUD-001、CON-001×3、MEM-002

二、G2 Gate 评估步骤

1. 验证 M2 全部 evidence 文件存在；
2. 在 Python 3.10/3.11/3.12 跑全量测试；
3. 确认所有 M2 PR 无 unresolved review threads；
4. 确认 develop 干净且 CI 全绿；
5. 创建 docs/testing/evidence/GATE-G2.md；
6. 更新 Plan/Status/Traceability/Handoff；
7. G2 PASS 后启动 M3 第一个 Work ID：CON-001 / Issue #32。

三、M3 串行顺序

CON-001 -> MEM-001 -> MEM-002 -> PLAN-001 -> PLAN-002 -> PLAN-003 -> CP-001
SES-001 -> AUD-001 -> OPS-001
CON-001 -> INTENT-001（可并行）
全部完成 -> M4

四、固定支持与发布边界

- Hermes 候选：v0.19.0 / Git tag v2026.7.20；
- Python 3.10：package/core/artifact-only；
- Python 3.11–3.12：完整 Hermes 候选；
- Runtime 当前 9 real Tools，目标 10；
- 当前 5 strict XFAIL owners：AUD-001、CON-001×3、MEM-002；
- 不提前合入 master，不提前 Tag/Release，不发布 PyPI；
- 不访问真实 HOME、DB、Memory、Secret。

五、执行纪律

- 一次只实施一个 Work ID 或评估一个 Gate；
- 最新 develop -> 专用分支 -> Draft PR -> TDD Red -> 最小实现 -> Required CI -> Code Review -> unresolved threads 0 -> expected-Head Squash Merge；
- 禁止 skip、弱化断言、删除测试、隐藏 XFAIL/XPASS；
- 每个 Work ID 建立 docs/testing/evidence/<WORK-ID>.md。

持续目标：G2 -> M3 -> M4/G3 -> master RC -> v3.0.0-beta.1 -> G4 -> Stable prep/SOAK/G5 -> v3.0.0。
```
