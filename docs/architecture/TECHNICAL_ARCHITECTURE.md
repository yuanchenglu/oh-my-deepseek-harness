# 技术架构：oh-my-deepseek-harness

- 文档状态：Target Architecture for Open-source Beta
- 适用分支：`develop`
- 目标：在不修改 Hermes 核心代码的前提下，建立可安装、可测试、可降级、无上下文数据损坏的 Harness Runtime。

## 1. 架构目标

### 1.1 功能目标

- 接收 Hermes Hook 事件并注入策略上下文；
- 维护 Session 级约束和任务策略；
- 安全压缩长上下文；
- 提供 Plan、Memory、Checkpoint 本地工具；
- 提供统一安装、诊断、日志和卸载能力。

### 1.2 非功能目标

| 属性 | 目标 |
|---|---|
| 正确性 | 不重复、不丢失必须保留的消息 |
| 隔离性 | Session、测试环境和用户数据隔离 |
| 可用性 | 辅助模块失败不得阻断 Hermes 主对话 |
| 可观测性 | 关键生命周期和降级均有结构化日志 |
| 可安装性 | Clean environment 可重复安装/卸载 |
| 可维护性 | Tool/API/Storage 单一契约源 |
| 安全性 | 默认仅 loopback；外部发送可见、可关闭 |
| 兼容性 | Python 3.10–3.12；明确 Hermes 兼容矩阵 |

## 2. 当前架构

```text
Hermes Agent
  │
  ├─ Plugin Hooks
  │    └─ plugins/deepseek-harness/
  │         gate / intent_router / reasoning_effort / latest_reminder
  │         assessor / learner / subagent_watch / tools
  │
  ├─ ContextEngine ABC
  │    └─ plugins/deepseek-context/
  │         DeepSeekContextEngine / DeepSeekCompressor
  │
  └─ Registered Tools
       └─ HTTP http://127.0.0.1:8200
            mcp/harness_server/
            FastAPI + SQLite
```

### 当前主要耦合

1. Plugin 通过文件相对路径管理 Server 进程；
2. Tool Schema 与 Pydantic Model 分离维护；
3. Gate 和 Assessor 通过模块级全局变量共享状态；
4. Context Engine 内同时承担压缩算法、状态管理、外部 API、完整性组装；
5. Server import 时执行数据库初始化和 Memory 导入；
6. 测试通过 `sys.path` 和动态 symlink 模拟真实 package。

## 3. 目标架构

```text
┌──────────────────────────────── Hermes Agent ────────────────────────────────┐
│                                                                              │
│  Hook Adapter                            Context Engine Adapter               │
│  ┌────────────────────────┐             ┌──────────────────────────────┐     │
│  │ Hermes payload mapping │             │ Hermes ContextEngine ABC     │     │
│  │ Hook result mapping    │             │ usage/model update adapter   │     │
│  └────────────┬───────────┘             └──────────────┬───────────────┘     │
└───────────────┼────────────────────────────────────────┼──────────────────────┘
                │                                        │
                ▼                                        ▼
┌──────────────────────────── Harness Core Library ─────────────────────────────┐
│ SessionPolicyService   IntentService     ContextIntegrityPipeline             │
│ ConstraintStore        StrategyService   CompressionPlanner                   │
│ ViolationEvaluator     TimeProvider      SummaryProvider                      │
│ EventWriter                               IntegrityValidator                   │
└───────────────────────────────┬────────────────────────────────────────────────┘
                                │
                ┌───────────────┴────────────────┐
                ▼                                ▼
┌────────────────────────┐        ┌──────────────────────────────────────────────┐
│ Local Tool Client      │        │ Harness Server Package                       │
│ health/readiness       │ HTTP   │ FastAPI App Factory                          │
│ typed request/response ├───────►│ PlanService / MemoryService / CheckpointSvc  │
│ process supervisor     │        │ Repository Layer / SQLite                    │
└────────────────────────┘        └──────────────────────────────────────────────┘
                                
External Summary Provider (optional)
  ContextIntegrityPipeline ── redaction/policy ──► DeepSeek/OpenAI-compatible API
```

## 4. 组件设计

## 4.1 Hermes Hook Adapter

职责仅限于：

- 从 `kwargs` 提取标准字段；
- 转换为内部 DTO；
- 调用 Harness Core Service；
- 将结果转换为 Hermes Hook 返回格式；
- 捕获异常并按策略降级。

禁止：

- 直接访问全局可变状态；
- 直接写用户文件；
- 在 Hook 中启动长时间进程；
- 重复实现业务规则。

### 标准 HookContext

```python
@dataclass(frozen=True)
class HookContext:
    session_id: str
    turn_id: str | None
    task_id: str | None
    user_message: str
    conversation_history: list[dict]
    is_first_turn: bool
    model: str | None
```

## 4.2 SessionPolicyService

负责：

- 约束提取；
- 约束按 Session 存储；
- Session 生命周期清理；
- 范围边界和策略上下文生成；
- Tool Call 约束匹配。

### 状态模型

```text
session_id
  ├─ constraints[]
  │    ├─ id
  │    ├─ source_turn_id
  │    ├─ original_text
  │    ├─ normalized_terms[]
  │    └─ created_at
  ├─ intent
  ├─ strategy
  └─ updated_at
```

默认使用进程内有界存储；需要跨进程恢复时才落 SQLite。必须设置 TTL 和 Session End 清理。

## 4.3 Constraint Event Log

运行时事件使用 JSONL，而不是把 Markdown 作为数据源。

```json
{"event":"constraint_violation","timestamp":"...","session_id":"...","constraint_id":"...","tool":"bash","evidence":"...","severity":"warning"}
```

Markdown 审计报告由事件日志生成，不参与反向解析。

## 4.4 IntentService

输入：用户消息和可选项目上下文。

输出：

```json
{
  "intent": "research",
  "confidence": 0.82,
  "matched_evidence": ["调研", "分析"],
  "alternatives": [{"intent":"architecture","score":0.31}],
  "strategy_id": "research-v1"
}
```

约束：

- 用户明确需求高于自动排除项；
- 低置信度返回 neutral/default，不伪造精确判断；
- 分类与推理提示映射分离；
- 规则配置需有 schema 校验和版本号。

## 4.5 ContextIntegrityPipeline

这是 Beta 的核心模块，必须从“压缩算法”升级为“带不变量检查的数据变换管线”。

```text
messages
  │
  ├─ 1. Normalize & assign stable IDs
  ├─ 2. Identify protected messages
  ├─ 3. Prune safe tool payloads
  ├─ 4. Select compression region
  ├─ 5. Redact outbound secrets
  ├─ 6. Generate summary
  ├─ 7. Assemble output
  ├─ 8. Integrity validation
  └─ 9. Commit or rollback
```

### 必须验证的不变量

- 最新用户消息出现一次且仅一次；
- 受保护消息原文全部存在；
- 非压缩区消息顺序一致；
- Tool Call ID 不重复；
- 所有 Tool Result 有对应 Tool Call；
- 摘要失败、校验失败或超时：返回原消息；
- 输出估算 Token 小于输入，否则返回原消息；
- 原输入对象不被原地修改。

### Provider 接口

```python
class SummaryProvider(Protocol):
    def summarize(self, request: SummaryRequest) -> SummaryResult: ...
```

Provider 负责 API；Pipeline 不直接 import OpenAI SDK。

### 外部发送策略

```yaml
summary:
  enabled: true
  provider: deepseek
  outbound_policy: redact
  redact_patterns: [api_key, bearer_token, private_key, env_secret]
  allow_tool_arguments: false
  fail_mode: preserve_original
```

## 4.6 Harness Server

### Package 结构

```text
src/harness_server/
├── __init__.py
├── __main__.py
├── app.py              # create_app(settings, repositories)
├── settings.py
├── api/
│   ├── plan.py
│   ├── memory.py
│   ├── checkpoint.py
│   └── health.py
├── domain/
│   ├── plan.py
│   ├── memory.py
│   └── checkpoint.py
├── services/
└── repositories/
    └── sqlite.py
```

### 启动方式

```bash
python -m harness_server
# 或
harness-server --host 127.0.0.1 --port 8200
```

### 生命周期

1. Plugin 初始化时调用 Supervisor；
2. Supervisor 请求 `/health`；
3. 未运行则启动子进程；
4. 循环请求 `/ready`，最长等待可配置；
5. 子进程 PID、日志路径和版本写入 runtime state；
6. Plugin 卸载或用户命令负责停止进程。

### 健康端点

- `/health`：进程存活；
- `/ready`：数据库迁移和 Service 可用；
- `/version`：Server、Schema、DB migration 版本。

默认响应不暴露本地绝对数据库路径。

## 4.7 Tool Contract

Pydantic Request Model 是唯一事实源。

```text
Pydantic Model
  ├─ FastAPI request validation
  ├─ JSON Schema for ctx.register_tool
  ├─ Client request typing
  └─ Contract tests
```

禁止手写重复 JSON Schema。

每个工具返回统一 envelope：

```json
{
  "ok": true,
  "data": {},
  "error": null,
  "meta": {"request_id":"...","server_version":"..."}
}
```

错误也必须保持工具返回字符串可解析，并区分：

- `validation_error`
- `not_found`
- `conflict`
- `server_unavailable`
- `timeout`
- `internal_error`

## 4.8 Plan Domain

### 不变量

- Step ID 在全库唯一；
- 依赖必须属于同一 Plan；
- 禁止自依赖；
- 更新后必须重新检测环；
- 删除/替换 Step 必须处理引用；
- 状态转换必须合法。

### Beta 范围

允许规则式任务分解，但必须诚实命名为 `rule_based_decomposition`。不宣称语义 DAG。用户可显式传入依赖关系。

## 4.9 Memory Domain

### 命令语义

- `memory_classify`：只返回分类，不写入；
- `memory_store`：分类、去重并持久化；
- `memory_query`：按层级/标签查询；
- `memory_filter`：按 λ 过滤；
- `memory_import`：显式或受控启动导入。

### 幂等键

```text
content_hash = SHA256(normalized_content + source_identity)
UNIQUE(content_hash)
```

保存：source path、mtime、import batch、原文长度、截断标志。

## 4.10 Checkpoint Domain

Checkpoint 必须是状态快照，不是“智能审查”的营销包装。

- 创建时校验 Plan 存在；
- completed IDs 必须属于 Plan；
- `checkpoint_number` 通过事务生成；
- Review 规则版本写入结果；
- 同一 Checkpoint + Rule Version 的审查应幂等。

## 5. 数据存储

### SQLite

适合 Beta 单机使用，但需要 migration 管理：

```text
schema_version
plans
steps
memories
checkpoints
constraint_events
runtime_state
```

### 事务边界

- 创建 Plan + Steps：单事务；
- 更新 Step + DAG 校验 + cascade：单事务；
- 创建 Checkpoint + number 分配：单事务；
- Memory import batch：单事务或可恢复批次。

### 数据目录

```text
~/.hermes/oh-my-deepseek-harness/
├── data/harness.db
├── logs/harness-server.log
├── events/constraint-events.jsonl
├── runtime/server.json
└── backups/
```

不要把运行数据写回 Git 仓库。

## 6. 配置体系

优先级：

```text
CLI arguments > environment variables > user config > package defaults
```

配置文件必须有 schema 和 `config_version`。

```yaml
config_version: 1
server:
  host: 127.0.0.1
  port: 8200
context:
  enabled: true
  fail_mode: preserve_original
summary:
  provider: deepseek
  outbound_policy: redact
memory:
  import_on_startup: false
```

## 7. 错误与降级策略

| 故障 | 降级 |
|---|---|
| Strategy YAML 无效 | 使用 neutral strategy |
| Summary API 不可用 | 返回原始 messages |
| Server 未启动 | Tool 返回结构化 unavailable，不阻断对话 |
| SQLite locked | 有界重试后返回错误，不吞异常 |
| Memory import 单文件失败 | 记录文件级错误，继续其他文件 |
| Constraint event 写入失败 | 记录 logger warning，不阻断工具 |
| Hook payload 缺字段 | 使用校验错误和安全默认值 |

禁止使用“异常全部静默吞掉”作为通用降级机制。

## 8. 安全架构

### 默认安全边界

- Server 绑定 `127.0.0.1`；
- 不启用 CORS；
- 非 loopback host 需要显式 `--allow-remote`；
- 数据库和日志权限限制为当前用户；
- API 响应不暴露 Secret 和绝对路径；
- 外部摘要默认做 Secret Redaction。

### 威胁模型

- Prompt 中包含 API Key；
- Tool result 读取 `.env`；
- 其他本机进程访问 8200 端口；
- 恶意 Plan 构造循环依赖；
- Memory 文件超大或重复导入；
- 日志注入和 Markdown 注入。

Beta 至少需要基础输入长度限制、敏感信息过滤和本机访问说明。

## 9. 可观测性

结构化日志字段：

```text
timestamp level component event session_id request_id duration_ms status error_code
```

关键事件：

- plugin_registered
- server_start_requested / ready / failed
- intent_classified
- constraint_added / violation_detected
- compression_started / committed / rolled_back
- memory_import_started / completed
- tool_request / tool_response

日志默认不写完整用户 Prompt、Secret 和 Tool Result。

## 10. 测试架构

### 测试分层

1. Pure Unit：规则、DAG、分类、边界；
2. Contract：Tool Schema ↔ Pydantic；
3. Storage Integration：临时 SQLite；
4. Process Integration：真实启动 Server；
5. Plugin Integration：Mock Hermes payload；
6. E2E：空 HOME 安装 → 调用 → 卸载；
7. Fault Injection：API 超时、SQLite lock、端口占用；
8. Compatibility：Python/Hermes/OS 矩阵。

### 隔离原则

- 每个测试使用临时 HOME；
- 禁止访问真实 `~/.hermes`；
- App 使用 factory；
- 外部 API 使用 fake provider；
- 不依赖测试期间创建源码目录 symlink。

## 11. 打包与发布

建议使用 `src/` layout，并提供 extras：

```toml
[project.optional-dependencies]
context = ["openai>=..."]
server = ["fastapi>=...", "uvicorn>=..."]
dev = ["pytest", "pytest-cov", "ruff", "mypy"]
all = ["oh-my-deepseek-harness[context,server]"]
```

安装脚本只做：

1. 环境检测；
2. Python package 安装；
3. Hermes Plugin 注册；
4. 配置与数据目录初始化；
5. Doctor 验证。

不要复制源码碎片到多个位置。

## 12. 架构演进顺序

1. 抽离 Context Integrity Validator；
2. Server package 化和 App Factory；
3. Tool Contract 单一源；
4. Session Store；
5. Memory 幂等；
6. Installer/Doctor；
7. 隐私和日志；
8. 才考虑新增算法能力。
