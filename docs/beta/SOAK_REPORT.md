# SOAK REPORT — Final RC 14-Day Stability Observation (SOAK-001)

- Work ID: `SOAK-001` · Issue: [#56](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/56)
- Status: **Complete（含 Owner 决策记录）**
- Final RC: `v3.0.0-beta.1`（master `a45eee0`；制品见 GitHub Release `v3.0.0-beta.1`）
- Observation window: 2026-08-05 → 2026-10-08（**64 个连续日历日**，≥ 计划要求的 14 天）

## 1. RC 冻结核验

自 `v3.0.0-beta.1` 发布（2026-08-05）至本次评估（2026-10-08）：

- **代码零变更**：develop 在发布后仅有文档/CI 维护提交（发布说明回填、状态行清理、同步提交），无 `src/`、插件、构建脚本变更；制品（wheel）内容不变。
- tag `v3.0.0-beta.1` 未被移动；发布制品哈希未变。
- 无 P0/P1 缺陷报告：open P0 = 0、open P1 = 0（复现查询见 `STABLE-001.md`）。

## 2. 日历达标

连续 64 个日历日 ≥ 14 天；期间无任何"代码或制品变更"事件（见 §1），未发生时钟重置。

## 3. 失败与完整性

- Beta Failure Ledger：**0 条**记录（`docs/beta/FAILURE_LEDGER.md`）。
- 无已确认的数据损坏或跨 Session 污染（0 报告）。
- 无 integrity P0。

## 4. 暴露量（§9 样本）— 未达标，Owner 决策豁免

计划 §9.2 要求的最小样本（10 名非维护者等）**当前收集为 0/N**（见 `VALIDATION_REPORT.md`）。本项目当前无外部用户基础，无法在合理期限内产生真实样本。

**Owner 决策（2026-10-08）**：接受以内部证据（完整测试矩阵、可复现 RC 构建、0 失败账本、0 P0/P1）作为 Stable 发布依据；将外部验证样本降级为 **post-release 持续观测项**（不阻塞发布）。决策与限制公开记录于：

- 本报告 §4；`VALIDATION_REPORT.md` §5；`docs/release/KNOWN_LIMITATIONS.md` §6；Issue #56 评论；GATE-G4。

## 5. 结论

**SOAK-001 Complete（owner decision）**：14 天日历 ✓ · RC 冻结 ✓ · 无 P0 ✓ · 暴露量按 owner 决策豁免并转为发布后观测（诚实记录，未达标事实不隐藏）。
