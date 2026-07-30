# 测试计划：oh-my-deepseek-harness

- 文档版本：2.1
- 适用分支：`develop`
- 目标版本：`v3.0.0-beta.1` / Python `3.0.0b1`
- 当前状态：100 个 Test ID 已登记；实现与 Release Gate 尚未通过

## 1. 测试原则

1. 数据完整性优先于覆盖率数字。
2. 不读取或修改真实 `~/.hermes`。
3. 外部依赖可 Fake，Release Test 单独使用受控真实依赖。
4. strict XFAIL 修复后删除，不得 skip 或弱化断言。
5. Release 证据必须来自 wheel/sdist 和冻结 Commit/RC Tag。
6. 当前 9 Tool、目标 10 Tool；`memory_store` 不在 M0 实现。
7. 10 Tool 目标名称的唯一机器可读来源是 `plugins/deepseek-harness/tools.py::TARGET_PUBLIC_TOOL_NAMES`；当前 Runtime 清单由目标清单减去显式 pending 集合派生。

## 2. 验证通道

| 通道 | 内容 |
|---|---|
| test-fast | Unit、Contract、静态检查、临时 SQLite；无网络和真实 HOME |
| test-integration | 真实 Server、wheel、临时 HOME install/doctor/smoke/uninstall |
| test-release | 冻结 Commit/RC Tag、Linux/macOS、Python Matrix、真实 Hermes、Migration、安全、SBOM、制品 |

G3 可使用冻结 Commit SHA 或可删除 RC Tag；正式不可变 Beta Tag 只在最终 `test-release` 通过后创建。

## 3. 环境隔离

```bash
HOME=$TMPDIR/home
HARNESS_CONFIG_PATH=$TMPDIR/data/config/config.yaml
HARNESS_DATA_ROOT=$TMPDIR/data
HARNESS_DB_PATH=$TMPDIR/data/harness.db
HARNESS_HOST=127.0.0.1
HARNESS_PORT=<dynamic-free-port>
DEEPSEEK_API_KEY=fake
```

## 4. 自动化用例矩阵

### 4.1 安装与生命周期

| ID | 场景 | 固定期望 | 主责 Work ID |
|---|---|---|---|
| `TC-INSTALL-001` | 空 HOME install dry-run | 文件树与持久状态不变 | `INS-001` |
| `TC-INSTALL-002` | 空 HOME 从 wheel 安装并 install | Plugin/Context/Server ready | `INS-001` |
| `TC-INSTALL-003` | 重复安装同版本 | 无重复配置、进程或导入 | `INS-001` |
| `TC-INSTALL-004` | 缺 Python 运行依赖 | 退出码 3，含恢复建议 | `INS-002` |
| `TC-INSTALL-005` | 端口占用 | 不启动双进程，诊断明确 | `INS-002` |
| `TC-INSTALL-006` | 普通卸载 | 移除部署，保留 distribution 与用户数据 | `INS-003` |
| `TC-INSTALL-007` | purge 卸载 | 仅删除规范化数据根且需确认 | `INS-003` |
| `TC-INSTALL-008` | 安装中断 | 可重试且无半配置 | `INS-003` |
| `TC-INSTALL-009` | Python/Hermes 不在支持矩阵 | install/doctor 非零退出并报告检测值和支持范围 | `INS-002` |
| `TC-INSTALL-010` | 捕获 lifecycle 子进程 | CLI 不调用 pip；普通 uninstall 打印 pip 卸载命令 | `INS-003` |

### 4.2 Session Policy

| ID | 场景 | 固定期望 | 主责 Work ID |
|---|---|---|---|
| `TC-POLICY-001` | A Session 有约束，B 无约束 | B 不继承 A | `SES-001` |
| `TC-POLICY-002` | 同 Session 新增约束 | 集合更新 | `SES-001` |
| `TC-POLICY-003` | 用户明确取消约束 | 对应约束失效 | `SES-001` |
| `TC-POLICY-004` | Session end | 内存状态清理 | `SES-001` |
| `TC-POLICY-005` | 两线程并发 Session | 无交叉污染 | `SES-001` |
| `TC-POLICY-006` | 路径疑似违反 | 写结构化事件 | `AUD-001` |
| `TC-POLICY-007` | 普通 Tool | 不误报 | `AUD-001` |
| `TC-POLICY-008` | JSONL 生成报告 | 数量字段一致 | `AUD-001` |

### 4.3 Intent Router

| ID | 场景 | 固定期望 | 主责 Work ID |
|---|---|---|---|
| `TC-INTENT-001` | 明确 research | research + 高证据 | `INTENT-001` |
| `TC-INTENT-002` | 明确 simple | simple | `INTENT-001` |
| `TC-INTENT-003` | 多类并列 | neutral/default | `INTENT-001` |
| `TC-INTENT-004` | 无关键词 | neutral/default | `INTENT-001` |
| `TC-INTENT-005` | 用户 override | 使用用户声明 | `INTENT-001` |
| `TC-INTENT-006` | 否定语义 | 不因关键词误判 | `INTENT-001` |
| `TC-INTENT-007` | 自动排除与显式要求冲突 | 用户要求优先 | `INTENT-001` |
| `TC-INTENT-008` | 无效策略 YAML | 安全默认 | `INTENT-001` |

### 4.4 Context Integrity

| ID | 场景 | 固定期望 | 主责 Work ID |
|---|---|---|---|
| `TC-CTX-001` | 阈值以下 | 返回原消息 | `CTX-004` |
| `TC-CTX-002` | 正常摘要 | Token 下降且完整性通过 | `CTX-004` |
| `TC-CTX-003` | Merge 分支 | 尾部消息不重复 | `CTX-001` |
| `TC-CTX-004` | Provider 超时 | 完整 rollback | `CTX-002` |
| `TC-CTX-005` | Provider 空响应 | 完整 rollback | `CTX-002` |
| `TC-CTX-006` | 缺 API Key | 不删消息且诊断 | `CTX-002` |
| `TC-CTX-007` | 硬约束在压缩区 | 逐字保留 | `CTX-003` |
| `TC-CTX-008` | 最新用户消息 | 恰好一次 | `CTX-003` |
| `TC-CTX-009` | Tool call/result | Pair 合法 | `CTX-003` |
| `TC-CTX-014` | 随机消息序列 | Property invariants 成立 | `CTX-003` |
| `TC-CTX-010` | Secret in Tool Result | 外发和日志脱敏 | `PRIV-001` |
| `TC-CTX-011` | 输出 Token 不降 | rollback | `CTX-004` |
| `TC-CTX-012` | 输入对象 | 不原地修改 | `CTX-004` |
| `TC-CTX-013` | 多 Session 多次压缩 | Summary 状态不串线 | `CTX-004` |

### 4.5 Tool Contract

目标名称由 `TARGET_PUBLIC_TOOL_NAMES` 固定为 10 个；`RUNTIME_PUBLIC_TOOL_NAMES` 必须等于目标集合减去 `PENDING_PUBLIC_TOOL_NAMES={memory_store}`。M0 只验证名称、分母和迁移状态，不要求 `memory_store` Handler/Schema 存在。

| ID | 场景 | 固定期望 | 主责 Work ID |
|---|---|---|---|
| `TC-CONTRACT-001` | plan_create 最小合法 payload | 非 422 且符合统一 envelope | `CON-001` |
| `TC-CONTRACT-002` | plan_update_step 最小合法 payload | 非 422 且符合统一 envelope | `CON-001` |
| `TC-CONTRACT-003` | plan_cascade 最小合法 payload | 非 422 且符合统一 envelope | `CON-001` |
| `TC-CONTRACT-004` | plan_status 最小合法 payload | 非 422 且符合统一 envelope | `CON-001` |
| `TC-CONTRACT-005` | memory_tag 最小合法 payload | 非 422 且符合统一 envelope | `CON-001` |
| `TC-CONTRACT-006` | memory_store 最小合法 payload | 非 422 且符合统一 envelope | `CON-001` |
| `TC-CONTRACT-007` | memory_query 最小合法 payload | 非 422 且符合统一 envelope | `CON-001` |
| `TC-CONTRACT-008` | memory_filter 最小合法 payload | 非 422 且符合统一 envelope | `CON-001` |
| `TC-CONTRACT-009` | checkpoint_create 最小合法 payload | 非 422 且符合统一 envelope | `CON-001` |
| `TC-CONTRACT-010` | checkpoint_review 最小合法 payload | 非 422 且符合统一 envelope | `CON-001` |

### 4.6 Plan

| ID | 场景 | 固定期望 | 主责 Work ID |
|---|---|---|---|
| `TC-PLAN-001` | Create Plan | Plan + Steps 单事务成功 | `PLAN-002` |
| `TC-PLAN-002` | 空任务 | 422 | `PLAN-002` |
| `TC-PLAN-008` | 非法状态转换 | conflict | `PLAN-002` |
| `TC-PLAN-010` | 并发更新 | 无半状态 | `PLAN-002` |
| `TC-PLAN-003` | 自依赖 | conflict | `PLAN-001` |
| `TC-PLAN-004` | 不存在依赖 | conflict | `PLAN-001` |
| `TC-PLAN-005` | 跨 Plan 依赖 | conflict | `PLAN-001` |
| `TC-PLAN-006` | 创建环 | conflict | `PLAN-001` |
| `TC-PLAN-007` | 更新形成环 | rollback | `PLAN-001` |
| `TC-PLAN-009` | Cascade strong/moderate/weak | 影响集合正确 | `PLAN-001` |
| `TC-PLAN-011` | 按 ID 查询 Plan | 返回完整图或 not_found envelope | `PLAN-003` |
| `TC-PLAN-012` | Archive 后默认 Query | 默认不返回，include-archived 可返回 | `PLAN-003` |
| `TC-PLAN-013` | 无确认后确认删除目标 Plan | 首次无变化；确认后只删目标 | `PLAN-003` |

### 4.7 Memory

| ID | 场景 | 固定期望 | 主责 Work ID |
|---|---|---|---|
| `TC-MEM-001` | Classify constraint | 层级和 evidence 正确 | `MEM-001` |
| `TC-MEM-002` | 无匹配 | unknown/default | `MEM-001` |
| `TC-MEM-003` | Store 同内容同来源两次 | 一条记录 | `MEM-001` |
| `TC-MEM-004` | 同内容不同来源 | 按 source identity 处理 | `MEM-001` |
| `TC-MEM-007` | λ 边界 0.3/0.4/0.7/0.8 | 无空区间 | `MEM-001` |
| `TC-MEM-008` | Query tags + layer | 交集正确 | `MEM-001` |
| `TC-MEM-010` | 10k 数据 | 满足 P95 目标 | `MEM-001` |
| `TC-MEM-005` | Import 重启三次 | 条目数不增加 | `MEM-002` |
| `TC-MEM-006` | 文件变更 | 更新或新版本，不重复旧数据 | `MEM-002` |
| `TC-MEM-009` | Delete by source | 仅删除目标 | `MEM-002` |
| `TC-MEM-011` | 默认配置启动三次 | 不扫描用户 Memory | `MEM-002` |
| `TC-MEM-012` | Import dry-run | 逐文件报告且 DB 字节/行数不变 | `MEM-002` |
| `TC-MEM-013` | 损坏 UTF-8/截断/取消 | 可诊断且无半批次 | `MEM-002` |

### 4.8 Checkpoint

| ID | 场景 | 固定期望 | 主责 Work ID |
|---|---|---|---|
| `TC-CP-001` | 合法 Plan 快照 | 成功 | `CP-001` |
| `TC-CP-002` | Plan 不存在 | not_found | `CP-001` |
| `TC-CP-003` | completed ID 不属于 Plan | conflict | `CP-001` |
| `TC-CP-004` | 并发编号 | 不重复 | `CP-001` |
| `TC-CP-005` | 同规则重复 Review | 幂等 | `CP-001` |
| `TC-CP-006` | Chain | 按编号升序 | `CP-001` |

### 4.9 Server

| ID | 场景 | 固定期望 | 主责 Work ID |
|---|---|---|---|
| `TC-SERVER-001` | Module/Console Script 启动 | ready | `RUN-001` |
| `TC-SERVER-002` | /health | 200 且不访问 DB/路径 | `RUN-001` |
| `TC-SERVER-003` | /ready DB 失败 | 503 server_unavailable | `RUN-001` |
| `TC-SERVER-004` | 重复启动 | 单进程 | `RUN-002` |
| `TC-SERVER-005` | 非 loopback 未授权 | 拒绝 | `SEC-002` |

### 4.10 安全

| ID | 场景 | 固定期望 | 主责 Work ID |
|---|---|---|---|
| `TC-SEC-001` | Secret redaction | 外发和日志无 Secret | `PRIV-001` |
| `TC-SEC-002` | 超长输入 | 422 | `SEC-002` |
| `TC-SEC-003` | SQL injection payload | 数据不受影响 | `SEC-002` |
| `TC-SEC-004` | Uninstall symlink/path traversal | 拒绝 | `SEC-002` |
| `TC-SEC-005` | 安装后权限 | 目录 0700；文件 0600 | `SEC-002` |
| `TC-SEC-006` | 摘要含 Prompt Injection 后请求破坏操作 | 不提升权限、不绕过 confirm | `SEC-002` |

### 4.11 Audit CLI

| ID | 场景 | 固定期望 | 主责 Work ID |
|---|---|---|---|
| `TC-AUDIT-CLI-001` | 手工 audit 并比较 scheduler | 报告生成且不修改 crontab/systemd/launchd | `OPS-001` |

### 4.12 Migration

| ID | 场景 | 固定期望 | 主责 Work ID |
|---|---|---|---|
| `TC-MIG-001` | 从 develop@37e4016 升级 | Config/DB/事件/进程迁移且 Doctor 绿 | `MIG-001` |
| `TC-MIG-002` | 重复 Memory dry-run 后迁移两次 | dry-run 不写；重复迁移不重复 | `MIG-001` |
| `TC-MIG-003` | 迁移 Markdown 约束日志 | 合法进 JSONL；非法原文件保留并报告 | `MIG-001` |
| `TC-MIG-004` | 旧 Server 运行时升级 | 停止旧进程且无双进程 | `MIG-001` |
| `TC-MIG-005` | 各阶段故障注入 | 恢复旧配置、DB 和可运行版本 | `MIG-001` |
| `TC-MIG-006` | 旧程序读新 Schema/无路径降级 | 启动前拒绝且不改数据 | `MIG-001` |

## 5. 当前 strict XFAIL 规范 ID

| XF ID | pytest node | 主责 |
|---|---|---|
| `XF-CTX-001` | `test_merge_path_does_not_duplicate_tail_messages` | `CTX-001` |
| `XF-CTX-002` | `test_summary_failure_preserves_original_messages` | `CTX-002` |
| `XF-CTX-003` | `test_hard_constraint_message_survives_verbatim` | `CTX-003` |
| `XF-POLICY-001` | `test_hard_constraints_are_isolated_between_sessions` | `SES-001` |
| `XF-AUDIT-001` | `test_immune_audit_parses_assessor_output_format` | `AUD-001` |
| `XF-CONTRACT-001` | `test_memory_filter_tool_uses_api_contract` | `CON-001` |
| `XF-CONTRACT-002` | `test_checkpoint_tool_schema_matches_api_required_fields` | `CON-001` |
| `XF-CONTRACT-003` | `test_plan_status_schema_matches_service_enum` | `CON-001` |
| `XF-INSTALL-001` | `test_install_script_installs_harness_server_runtime` | `PKG-001` |
| `XF-DEPS-001` | `test_runtime_dependencies_include_openai` | `PKG-002` |
| `XF-RELEASE-001` | `test_project_versions_are_consistent` | `REL-001` |
| `XF-MEM-001` | `test_memory_import_storage_is_idempotent` | `MEM-002` |

历史别名 `XF-PKG-001`、`XF-VERSION-001` 只用于定位 v2.2，不得用于新 Issue/证据。

## 6. CI 与退出标准

### G0
- 100 个 Test ID 唯一且各有唯一主责。
- 版本、Tool、CLI、路径、支持范围和安全默认值在规格文档中一致。
- `TARGET_PUBLIC_TOOL_NAMES` 精确包含 10 个唯一名称；当前注册集合精确为目标集合减去 `memory_store`。

### Public Beta
- Release Test Failed = 0、XPASS = 0、XFAIL = 0。
- P0 = 0；P1 关闭或有有效 Waiver。
- 10 个 Tool Contract、Context、Session、Migration、安全、Linux/macOS、Python Matrix、真实 Hermes 全部通过。

### Stable
- P0 = 0、P1 = 0。
- 最终 RC 连续 14 天达到计划暴露量。
- 安全、许可证、依赖和迁移审查完成。

## 7. 测试报告格式

每个 RC 报告包含 Commit SHA、环境 Matrix、Passed/Failed/XPASS/XFAIL/Skipped、P0/P1、未执行项、Run/Artifact、与上一版本差异和 Release 建议。
