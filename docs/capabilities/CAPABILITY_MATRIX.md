# Capability Matrix

本矩阵按 `STATUS.md` 的五级状态，对项目对外宣称的每一项能力进行分级，并链接到对应证据。任何能力行不得使用超出证据的表述。

> 状态定义见 [STATUS.md](STATUS.md)。证据文件位于 `docs/testing/evidence/`。

## 能力分级矩阵

| 能力 | 状态 | 证据 | 说明 |
|------|------|------|------|
| 认知门控（L1/L2/L3 导航） | Beta | `docs/testing/evidence/GATE-G0.md` | 契约测试通过；真实 Hermes E2E 由 `COMPAT-001` 验证 |
| 约束免疫系统（I-01） | Beta | `docs/testing/evidence/AUD-001.md`、`docs/testing/evidence/OPS-001.md` | JSONL 事件源 + 手工审计命令；cron 为可选手动安装 |
| 意图路由（I-10 7+1 分类） | Beta | `docs/testing/evidence/INTENT-001.md` | 低置信回退、否定语义、用户显式优先已修复 |
| 推理强度路由（I-17） | Degraded | `docs/testing/evidence/INTENT-001.md` | API `reasoning_effort` 受 Hook 协议限制，降级为上下文提示注入 |
| 时效信息注入（I-18） | Degraded | `docs/testing/evidence/INTENT-001.md` | API 拒绝 `role=latest_reminder`，降级为上下文文本注入 |
| 工具质量评估（assessor） | Beta | `docs/testing/evidence/QA-ART-001.md` | 工具调用后内容完整性检查 |
| 会话学习（I-09） | Experimental | `docs/testing/evidence/RUN-001.md` | 仅记录 Session 结束 + 超 10 轮输出 Skill 候选日志；不自动创建 Skill（见 CR-P2-001） |
| 子任务监控（subagent_watch） | Beta | `docs/testing/evidence/RUN-001.md` | 记录子任务启停与结果 |
| 上下文压缩引擎（I-03/04/07/13） | Beta | `docs/testing/evidence/CTX-001.md`、`docs/testing/evidence/CTX-002.md`、`docs/testing/evidence/CTX-003.md`、`docs/testing/evidence/CTX-004.md` | 独立 LLM 客户端，输入不可变 |
| 级联规划（I-06 plan 工具） | Beta | `docs/testing/evidence/PLAN-001.md`、`docs/testing/evidence/PLAN-002.md`、`docs/testing/evidence/PLAN-003.md`、`docs/testing/evidence/CP-001.md` | 状态机、依赖校验、Cascade 影响集合 |
| 记忆标签/过滤（I-12 memory 工具） | Beta | `docs/testing/evidence/MEM-001.md`、`docs/testing/evidence/MEM-002.md` | memory_tag/query/filter 已注册；store 未注册 |
| 记忆存储（memory_store） | Experimental | `docs/testing/evidence/CON-001.md`、`docs/testing/evidence/MEM-001.md` | Schema/Contract 已定，领域逻辑已实现，但 handler 未注册为运行时 Tool |
| 安装/生命周期（INS） | Beta | `docs/testing/evidence/INS-001.md`、`docs/testing/evidence/INS-002.md`、`docs/testing/evidence/INS-003.md` | 安装备份、生命周期、Doctor |
| 包/制品（PKG） | Beta | `docs/testing/evidence/PKG-001.md`、`docs/testing/evidence/PKG-002.md` | 包级 CI 与制品校验 |
| 隐私/上下文（PRIV） | Beta | `docs/testing/evidence/PRIV-001.md` | 上下文隐私边界测试 |
| 版本语义（REL） | Beta | `docs/testing/evidence/REL-001.md` | 版本统一策略 |

## 已移除 / 不可行能力

| 能力 | 状态 | 证据 | 说明 |
|------|------|------|------|
| I-14 推理过程剥离 | Removed | `docs/testing/evidence/REL-003.md` | 死代码 + 与 V4 API 设计冲突，已移除 |
| I-15 DSML 工具调用优化 | Removed | `docs/testing/evidence/REL-003.md` | 服务端自动转换，无需客户端解析 |
| I-16 Quick Instruction 路由 | Removed | `docs/testing/evidence/REL-003.md` | V4 内部机制，无法经 OpenAI 兼容 API 实现，由 I-10 替代 |

## 未完成 / 待验证能力

下列能力当前为 **Experimental** 或 **Beta**，在 `COMPAT-001`（真实 Hermes E2E）完成前不得标为 Stable：

- 完整 Hermes 集成（v0.19.0 + Python 3.11-3.12）：Beta — 见 `docs/testing/evidence/COMPAT-000.md`
- `memory_store`：Experimental — 见 `docs/testing/evidence/CON-001.md`、`MEM-001.md`

## 收敛原则

- 本矩阵是能力宣称的权威来源；README 只做摘要并链接本矩阵；
- 任何新增能力必须先有状态与证据，才能进入本矩阵；
- 绝对化表述（唯一、零副作用、永不冲突、自动学习）不入本矩阵。