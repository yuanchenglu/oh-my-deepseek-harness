# 新会话交接提示词

> 状态：**计划已完成**（2026-10-08，v3.0.0 已发布）；本文件保留为"发布后维护"入口。

## 一、当前事实（2026-10-08 发布）

- GitHub 仓库：`yuanchenglu/oh-my-deepseek-harness`
- **v3.0.0（Stable）已发布**；48/48 Work IDs Complete；G0–G5 全部 PASS。
- 唯一豁免：外部验证样本按 **owner 决策豁免**（0/N，事实与决策均公开记录）——详见 `docs/testing/evidence/GATE-G4.md`、`docs/beta/SOAK_REPORT.md`、`docs/release/KNOWN_LIMITATIONS.md` §6。
- 事实源优先级：GitHub 远程事实 > `OPEN_SOURCE_RELEASE_PLAN.md`（v2.3.35）> EXECUTION_STATUS / Traceability / Gate Evidence > 产品与架构规范。

## 二、发布后维护事项（新会话若继续）

1. **外部验证观测**：若有真实用户数据，按 `docs/beta/METRICS_SCHEMA.md`（§9.3 隐私约束，opt-in）收集并更新 `docs/beta/VALIDATION_REPORT.md`。
2. **缺陷修复**：走 develop PR 流程（见 `CONTRIBUTING.md`）；发布相关按 `docs/release/ROLLBACK.md`（不可变：撤回=新版本）。
3. `memory_store` handler 注册属后续版本范围（见 Known Limitations）。
4. PyPI 保持禁用（`REL-005`），除非另行完成核验与授权。

## 三、关键文档索引

- 计划：`docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md`（v2.3.35，含 G4 owner decision 记录）
- 状态：`docs/roadmap/EXECUTION_STATUS.md`
- 追踪：`docs/traceability/RELEASE_TRACEABILITY.md`
- 发布记录：`docs/testing/evidence/REL-008.md`、`docs/release/RELEASE_NOTES_v3.0.0.md`
- 发布安全清单：`docs/release/RELEASE_CHECKLIST.md`（v3.0.0 发布记录段）
