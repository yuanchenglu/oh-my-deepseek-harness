# 技术架构：oh-my-deepseek-harness

- 文档状态：Target Architecture for Open-source Beta
- 目标版本：`v3.0.0-beta.1`
- 适用分支：`develop`
- 当前成熟度：Experimental Preview；G0 尚未通过

## 1. 架构目标

在不修改 Hermes 核心代码的前提下，建立可安装、可测试、可降级、可迁移、无上下文数据损坏的本地 Harness Runtime。

| 属性 | 目标 |
|---|---|
| 正确性 | 消息不丢失、不重复，Tool Pair 合法 |
| 隔离性 | Session、测试 HOME、DB 和端口隔离 |
| 可用性 | 辅助模块失败不阻断 Hermes 主对话 |
| 可观测性 | 生命周期和降级有结构化日志与错误码 |
| 可安装性 | 从 wheel/sdist 在源码目录外运行 |
| 可维护性 | Tool/API/Storage 单一模型源 |
| 安全性 | loopback、最小权限、外发 opt-in + redaction |
| 兼容性 | Linux/macOS、Python 3.10–3.12、单一 Hermes 正式版本 |

## 2. 固定外部契约

- Git Tag `v3.0.0-beta.1`；Python `3.0.0b1`；Plugin `3.0.0-beta.1`。
- 当前 9 个 Tool；目标 10 个，新增 `memory_store` 在 M3 实现。
- pip 只管理 distribution；CLI 不得调用 pip 管理自身。
- 环境变量只使用计划 §2.8 的稳定名称，不保留 `HARNESS_SERVER_PORT` / `HARNESS_SERVER_URL`。
- G3 从冻结 Commit SHA 或临时 RC Tag 构建；正式 Tag 由 `BETA-001` 创建。

## 3. 目标源码布局

```text
src/
├── deepseek_harness/
│   ├── adapters/          # Hermes Hook 与 Tool Client
│   ├── session_policy.py
│   ├── intent_router.py
│   ├── audit_events.py
│   ├── cli.py
│   ├── installer.py
│   ├── doctor.py
│   ├── migration.py
│   └── resources/
├── deepseek_context/
│   ├── adapters/
│   ├── pipeline.py
│   ├── planner.py
│   ├── redaction.py
│   ├── provider.py
│   ├── validator.py
│   └── resources/
└── harness_server/
    ├── __main__.py
    ├── app.py
    ├── settings.py
    ├── models.py
    ├── schema.py
    ├── services/
    └── repositories/sqlite.py
```

旧 `plugins/*` 只保留 Hermes 要求的 manifest 和薄转发；`mcp/harness_server` 不保留第二份业务源码。

## 4. 运行架构

```text
Hermes
 ├─ Hook Adapter ──► Harness Core Services
 ├─ Context Adapter ──► ContextIntegrityPipeline ──► optional Summary Provider
 └─ Tool Registration ──► Local Tool Client ──HTTP──► Harness Server ──► SQLite

CLI ──► Installer / Doctor / Supervisor / Migration / Audit
```

### 4.1 Hook Adapter

只负责 payload 映射、DTO 转换、调用服务、结果映射和异常降级；不得直接访问全局状态、写用户文件或启动长进程。

### 4.2 SessionPolicyStore

以 `session_id` 为键保存 constraints、intent、strategy、updated_at；支持显式取消、TTL、session-end cleanup 和并发隔离。

### 4.3 ContextIntegrityPipeline

```text
messages
  → normalize + stable IDs
  → identify protected messages
  → prune safe tool payloads
  → select compression region
  → redact outbound secrets
  → summarize
  → assemble
  → validate invariants
  → commit or return original
```

不变量：最新请求恰好一次；受保护原文存在；非压缩区顺序不变；Tool Call/Result 成对；ID 唯一；输出 Token 下降；输入对象不变；任何异常完整 rollback。

### 4.4 Summary Provider

Provider 通过 Protocol 注入；Pipeline 不直接依赖 SDK。默认禁用；外发策略固定 `redact`，Tool 参数默认不外发，诊断事件不含原 Prompt。

### 4.5 Harness Server

- `create_app(settings, repositories)` 装配；import 无副作用。
- Supervisor 先 `/health`，必要时启动，再等待 `/ready`。
- PID、版本和日志写入 `runtime/server.json` 与 `logs/harness-server.log`。
- 重复 start 只有一个进程；stop 幂等。

探针：

| Endpoint | 成功语义 | 失败语义 |
|---|---|---|
| `/health` | Event Loop alive | 不访问 DB/Provider |
| `/ready` | DB、migration、service ready | 503 + `server_unavailable` |
| `/version` | distribution/server/config/db/Hermes 版本 | 不暴露路径或 Secret |

### 4.6 Tool Contract

Pydantic Request Model 是唯一事实源，并生成 FastAPI validation、Hermes JSON Schema、Client typing 和 Contract Test。

目标 Tool：`plan_create`、`plan_update_step`、`plan_cascade`、`plan_status`、`memory_tag`、`memory_store`、`memory_query`、`memory_filter`、`checkpoint_create`、`checkpoint_review`。

统一 envelope：

```json
{"ok": true, "data": {}, "error": null, "meta": {"request_id": "...", "server_version": "..."}}
```

错误码固定为 validation_error、not_found、conflict、server_unavailable、timeout、internal_error。

## 5. 数据域不变量

### Plan

依赖存在且同 Plan；禁止自依赖和环；状态转换合法；Create/Update/Cascade 原子；Archive 默认保留；Delete 需确认且只影响目标 Plan。

### Memory

`content_hash = SHA256(normalized_content + source_identity)`；保存 source、mtime、batch；启动导入默认关闭；dry-run 不写 DB；Import 单文件失败不产生半批次。

### Checkpoint

Plan 存在；completed ID 归属；同 Plan 并发编号唯一；规则版本参与幂等；Chain 有序。

### Audit

JSONL 是唯一事件源；Markdown 只作为派生报告；损坏行可诊断且不破坏其余事件。

## 6. 配置、安全与数据根

```text
~/.hermes/oh-my-deepseek-harness/
├── config/config.yaml
├── data/harness.db
├── logs/harness-server.log
├── events/constraint-events.jsonl
├── runtime/server.json
└── backups/
```

目录 `0700`，文件 `0600`。配置优先级 CLI > Environment > User Config > Defaults。外部 `HARNESS_DB_PATH` 和 symlink 越界路径不进入 purge 范围。

安全默认：loopback；Summary false；Tool args false；Memory startup import false；log content false。破坏性命令缺 `--confirm` 返回 2 且无变化。

## 7. 安装、升级与卸载

1. pip 安装 distribution。
2. CLI dry-run 输出影响范围。
3. install 部署 Hermes 薄入口、配置和数据目录。
4. Supervisor 启动并 Doctor。
5. upgrade 备份、迁移、验证；失败 rollback。
6. 普通 uninstall 移除部署和 runtime state，保留 distribution 与数据。
7. 用户显式执行 pip uninstall；purge 另需 `--confirm`。

## 8. 测试与发布架构

- `test-fast`：Unit/Contract/静态检查，无网络和真实 HOME。
- `test-integration`：真实 Server、wheel、临时 HOME E2E。
- `test-release`：冻结 Commit/RC Tag，Linux/macOS、Python Matrix、真实 Hermes、Migration、安全、SBOM 和制品完整性。

G3 生成 RC 制品；G3 通过后合入 master，再对精确 Commit 运行最终 `test-release`；通过后 `BETA-001` 创建不可变 Tag/Release。

## 9. 明确不做

不修改 Hermes 核心；不做远程 Server、云账号、多租户、UI、容器编排、复杂 LLM DAG、自动 Skill 执行或新 Innovation。
