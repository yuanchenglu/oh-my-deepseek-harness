# 产品架构：oh-my-deepseek-harness

- 文档状态：Draft for Open-source Beta
- 目标版本：`v0.3.0-beta`
- 适用分支：`develop`
- 产品定位：面向 Hermes Agent + DeepSeek 的本地 Harness 增强套件

## 1. 产品定义

`oh-my-deepseek-harness` 不是一个独立 Agent，也不是 DeepSeek API SDK。它是运行在 Hermes Agent 周边的 Harness 增强层，通过 Plugin Hook、Context Engine 和本地 Tool Service 改善以下问题：

1. 用户约束在长任务中被遗忘或误执行；
2. 不同任务复杂度使用相同推理策略；
3. 长会话上下文膨胀，历史事实和工具结果难以管理；
4. Memory 缺少分层、过滤和可解释检索；
5. 多步骤计划修改后，依赖影响不可见；
6. 长任务缺少阶段性 Checkpoint 和可回顾状态。

产品价值不是“提供更多工具”，而是提高 Agent 的四项基础质量：

- **遵约性**：用户明确约束不被遗忘；
- **完整性**：上下文压缩不损坏事实；
- **可控性**：计划、记忆和审查可追踪；
- **经济性**：在不损失正确性的前提下降低无效上下文和过度推理。

## 2. 目标用户

### Persona A：个人开发者

- 使用 Hermes Agent + DeepSeek 完成代码、研究或自动化任务；
- 希望安装简单、成本低、行为可控；
- 无能力维护多个 MCP 服务和复杂配置。

### Persona B：Agent 高强度用户

- 长时间运行 Agent，会遇到上下文、计划漂移和 Memory 污染；
- 需要看到 Agent 为什么采用某种策略；
- 愿意使用高级配置和诊断工具。

### Persona C：Harness 研究者/贡献者

- 关注 Context Engineering、Memory、Plan、Tool Use；
- 需要可独立运行、可测试、可替换的实验模块；
- 希望基于明确契约贡献算法，而不是修改一体化代码。

### 非目标用户

- 不使用 Hermes Agent 的普通聊天用户；
- 需要企业级多租户、权限、审计合规平台的团队；
- 希望获得完整 IDE、桌面端或通用 Agent 产品的用户；
- 期望插件自动修改生产环境而无需确认的用户。

## 3. 产品边界

### 3.1 产品内

- Hermes Plugin Hook 注入；
- 约束提取、Session 隔离和违规事件记录；
- 意图分类和推理提示路由；
- Context 压缩与完整性校验；
- 本地 Plan、Memory、Checkpoint 工具；
- 安装、诊断、卸载和迁移；
- 本地日志和可复现测试。

### 3.2 产品外

- 不修改 Hermes 核心代码；
- 不训练或微调 DeepSeek 模型；
- 不承诺直接设置 Hermes 未暴露的模型 API 参数；
- 不提供独立聊天 UI；
- 不提供云端账号、同步、多租户和权限系统；
- 不自动创建未经用户确认的 Skill；
- 不承担生产级工作流编排平台职责。

## 4. 产品能力域

```text
用户任务
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ A. Session Policy                                      │
│ 约束提取 · 范围边界 · 时间上下文 · 意图识别             │
└──────────────────────┬──────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│ B. Reasoning Guidance                                  │
│ 任务复杂度 → 策略提示 · 推理深度建议 · 审查标准          │
└──────────────────────┬──────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│ C. Context Integrity                                   │
│ Token 预算 · 工具结果裁剪 · 摘要 · 约束逐字保留 · 降级   │
└──────────────────────┬──────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│ D. Local Harness Tools                                 │
│ Plan DAG · Memory 分类/存储/查询 · Checkpoint            │
└──────────────────────┬──────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│ E. Observability & Lifecycle                           │
│ 安装 · 健康检查 · 日志 · 测试 · 卸载 · 数据迁移          │
└─────────────────────────────────────────────────────────┘
```

## 5. 核心用户旅程

### Journey 1：安装与首次验证

1. 用户克隆仓库；
2. 执行 `install.sh --dry-run`；
3. 系统展示将安装的文件、依赖、端口和数据目录；
4. 用户正式安装；
5. 安装器注册 Plugin、Context Engine 和 Harness Server；
6. 安装器执行健康检查；
7. 用户运行诊断命令看到所有组件状态。

**成功标准**：全新环境下 10 分钟内完成，失败时有明确日志和恢复方法。

### Journey 2：执行带硬约束的任务

1. 用户声明“只修改文档，不能修改业务代码”；
2. Session Policy 将约束绑定到当前 Session；
3. 每次高风险 Tool 调用前后进行匹配；
4. 命中疑似冲突时记录事件并提示模型/用户；
5. Session 结束后清理内存状态，保留结构化审计记录。

**成功标准**：约束不跨 Session；无静默污染；所有告警可追踪来源。

### Journey 3：长会话触发压缩

1. Context 达到阈值；
2. 系统识别必须原样保留的消息；
3. 裁剪可安全压缩的旧 Tool Result；
4. 调用摘要模型；
5. 校验输出无重复、无约束丢失、Tool Pair 合法；
6. 校验失败或 API 失败时回退原始消息。

**成功标准**：压缩只能降低上下文体积，不能损坏对话状态。

### Journey 4：使用 Plan / Memory / Checkpoint

1. LLM 根据 Tool Schema 创建 Plan；
2. 用户或 LLM 更新步骤；
3. Server 验证 DAG 不变量并返回影响范围；
4. 关键阶段创建 Checkpoint；
5. Memory 可分类、持久化、去重和检索；
6. 用户可查询状态并清理数据。

**成功标准**：Tool Schema、API Model、存储模型完全一致。

## 6. 产品模块

| 模块 | 用户可见价值 | 当前状态 | Beta 目标 |
|---|---|---|---|
| Cognitive Gate | 固定认知提醒和任务边界 | 已实现原型 | 可配置、可关闭 |
| Constraint Guard | 记录硬约束与疑似违反 | 不安全的全局状态 | Session 隔离 + JSONL |
| Intent Router | 给不同任务不同策略 | 规则原型 | 可解释分类 + 低置信回退 |
| Reasoning Guidance | 文本提示控制推理深度 | 降级实现 | 明确标注“提示级” |
| Latest Reminder | 注入当前时间 | 已实现 | 时区明确、可配置 |
| Context Engine | 压缩长上下文 | 存在数据损坏风险 | Integrity-first |
| Plan Engine | 多步骤计划与影响传播 | 线性链原型 | DAG 不变量完整 |
| Memory Service | 记忆分类和过滤 | 导入不幂等 | 分类/写入/查询闭环 |
| Checkpoint Review | 阶段状态快照 | 规则原型 | 可解释、可回放 |
| Installer/Doctor | 安装和诊断 | 不完整 | 单命令可验证 |

## 7. 版本产品策略

### v0.3.0-beta：可信运行

只解决：

- 安装可用；
- Context 不损坏数据；
- Session 状态隔离；
- Tool 契约一致；
- Memory 幂等；
- 文档真实。

不增加新的 Innovation 编号。

### v0.4.0-beta：可观测与兼容

- Doctor 命令；
- 结构化日志；
- Hermes 版本兼容矩阵；
- Linux/macOS 测试；
- 配置迁移。

### v1.0.0：开源稳定版

只有在真实用户完成安装、长会话和 Tool 调用验证后发布。

## 8. 产品原则

1. **Integrity before compression**：宁可不压缩，也不能丢历史。
2. **Explicit over magical**：降级实现必须明确，不包装为原生 API 能力。
3. **Session-scoped by default**：所有运行时状态默认绑定 Session。
4. **Single source of contract**：Tool、API、存储使用统一模型。
5. **Local-first, transparent outbound**：本地优先；外部数据发送必须可见、可关闭。
6. **Evidence-based claims**：README 的每项能力都要有测试或运行证据。
7. **Fewer features, complete loops**：不追求 Innovation 数量，优先完成闭环。

## 9. 产品成功指标

### 北极星指标

**有效 Harness 会话率**：安装成功且在无数据完整性错误的情况下完成任务的会话占比。

### Beta 指标

| 指标 | 目标 |
|---|---:|
| Clean install 成功率 | 100%（CI 支持环境） |
| Harness Server readiness 成功率 | 100% |
| Tool Schema 契约通过率 | 100% |
| Context 数据完整性回归通过率 | 100% |
| Session 隔离测试通过率 | 100% |
| Memory 重复导入率 | 0% |
| 未解释外部数据发送 | 0 次 |
| P0 未关闭数量 | 0 |

## 10. 产品决策记录

### ADR-P-001：停止扩展 Innovation 编号

在 Runtime Integrity 完成前不新增 I-19 及以后功能。

### ADR-P-002：版本回归 Beta 语义

当前 `2.x` 容易让用户误判成熟度。建议下一公开版本使用清晰的 Beta 标识，是否重置为 `0.x` 由维护者最终决定。

### ADR-P-003：Skill 自动创建不进入 Beta

Beta 只提供候选提议和证据，不自动写入可执行 Skill。

### ADR-P-004：Harness Server 保持本地单进程

开源首版不拆分微服务，不引入容器编排、消息队列和云端控制面。
