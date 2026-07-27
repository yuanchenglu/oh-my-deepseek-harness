# 测试计划：oh-my-deepseek-harness

- 文档版本：1.0
- 适用分支：`develop`
- 测试目标：证明项目具备开源 Beta 所需的安装、运行、完整性、隔离性和故障降级能力
- 需求基线：`docs/product/PRD.md`

## 1. 测试原则

1. 正确性和数据完整性优先于覆盖率数字；
2. 测试不得读取或修改开发者真实 `~/.hermes`；
3. 每个外部依赖必须可替换为 Fake；
4. 已确认缺陷必须转化为可执行回归测试；
5. 合法 Tool Schema 输入必须通过 API；
6. 故障测试必须验证降级结果，而不只是“不抛异常”；
7. Release 测试必须从空环境安装，而不是从源码目录直接 import。

## 2. 测试层级

| 层级 | 目标 | 工具 |
|---|---|---|
| L0 Static | 语法、风格、类型、依赖 | Ruff、mypy/pyright、ShellCheck、pip-audit |
| L1 Unit | 纯函数和领域规则 | pytest |
| L2 Contract | Tool/Pydantic/Storage 契约 | pytest + JSON Schema |
| L3 Storage Integration | SQLite 事务、幂等、迁移 | pytest + tmp_path |
| L4 Process Integration | 真实 Server 进程和 HTTP | subprocess + httpx |
| L5 Plugin Integration | Hook payload 和生命周期 | Fake Hermes Context |
| L6 Install E2E | dry-run/install/doctor/uninstall | shell + 临时 HOME |
| L7 Fault Injection | API 超时、端口占用、DB lock | Fake Provider + subprocess |
| L8 Compatibility | Python、OS、Hermes 矩阵 | GitHub Actions |

## 3. 测试环境

### CI Matrix

- Ubuntu latest
- Python 3.10
- Python 3.11
- Python 3.12

### Release 前人工/自托管 Matrix

- macOS latest + Python 3.11/3.12
- 一个明确的 Hermes 正式版本
- DeepSeek API Sandbox/低风险账号

### 测试隔离

每个测试进程必须设置：

```bash
HOME=$TMPDIR/home
HARNESS_DB_PATH=$TMPDIR/harness.db
HARNESS_PORT=<dynamic-free-port>
DEEPSEEK_API_KEY=fake
```

禁止：

- 使用默认用户 HOME；
- import 时自动扫描真实 Memory；
- 依赖源码目录 symlink 才能 import；
- 访问真实外部 API 的普通 CI。

## 4. 测试数据

### Context 数据集

- 中英文混合消息；
- 连续相同 role；
- Tool call/result；
- 多个 Tool call；
- 空 Content；
- List Content；
- 大 Tool Result；
- 含硬约束；
- 含 Secret；
- 最新 Pending Ask；
- Summary Provider 空响应/超时/异常。

### Intent 数据集

每类不少于 50 条，并包含：

- 单一意图；
- 多意图冲突；
- 无关键词；
- 用户显式声明；
- 中英文；
- 宽泛词“项目、更新、系统、方案”；
- 否定表达，例如“不要做架构设计”。

### Memory 数据集

- 相同内容相同来源；
- 相同内容不同来源；
- 文件内容变更；
- 超长段落；
- Markdown 标题；
- 中文和英文标签；
- 损坏 UTF-8；
- 10,000 条性能集。

## 5. 自动化用例清单

## 5.1 安装与生命周期

| ID | 用例 | 期望 | 优先级 |
|---|---|---|---|
| TC-INSTALL-001 | 空 HOME dry-run | 无文件变化 | P0 |
| TC-INSTALL-002 | 空 HOME install | Plugin/Context/Server 就绪 | P0 |
| TC-INSTALL-003 | 重复安装 | 无重复配置和进程 | P0 |
| TC-INSTALL-004 | 缺 Python 依赖 | 明确错误和安装建议 | P0 |
| TC-INSTALL-005 | 端口被占用 | 不启动第二进程，明确诊断 | P0 |
| TC-INSTALL-006 | 普通卸载 | 程序移除、数据保留 | P0 |
| TC-INSTALL-007 | purge 卸载 | 只删除产品已知目录 | P1 |
| TC-INSTALL-008 | 安装中断 | 可重试，无半配置 | P1 |

## 5.2 Session Policy

| ID | 用例 | 期望 | 优先级 |
|---|---|---|---|
| TC-POLICY-001 | A Session 声明约束，B 无约束 | B 不继承 A | P0 |
| TC-POLICY-002 | 同 Session 新增约束 | 约束集合更新 | P0 |
| TC-POLICY-003 | 用户明确取消约束 | 对应约束失效 | P1 |
| TC-POLICY-004 | Session end | 内存状态清理 | P0 |
| TC-POLICY-005 | 两线程并发 Session | 无交叉污染 | P0 |
| TC-POLICY-006 | 文件路径疑似违反 | 生成结构化事件 | P1 |
| TC-POLICY-007 | 普通 Tool | 不误报 | P1 |
| TC-POLICY-008 | JSONL → 审计报告 | 数量和字段一致 | P1 |

## 5.3 Intent Router

| ID | 用例 | 期望 |
|---|---|---|
| TC-INTENT-001 | 明确 research | research，高证据 |
| TC-INTENT-002 | 明确 simple | simple |
| TC-INTENT-003 | 多类并列 | neutral/default |
| TC-INTENT-004 | 无关键词 | neutral/default |
| TC-INTENT-005 | 用户显式 override | 使用用户声明 |
| TC-INTENT-006 | 否定语义 | 不因关键词错误分类 |
| TC-INTENT-007 | 自动排除与用户要求冲突 | 用户要求优先 |
| TC-INTENT-008 | 配置 YAML 无效 | 安全默认策略 |

输出 confusion matrix、macro F1 和低置信回退率。Beta 不要求机器学习模型，但规则性能必须可量化。

## 5.4 Context Integrity

| ID | 用例 | 期望 | 优先级 |
|---|---|---|---|
| TC-CTX-001 | 阈值以下 | 返回原始消息 | P0 |
| TC-CTX-002 | 正常摘要 | Token 减少且完整性通过 | P0 |
| TC-CTX-003 | Merge 分支 | 尾部消息不重复 | P0 |
| TC-CTX-004 | Provider 超时 | 完整 rollback | P0 |
| TC-CTX-005 | Provider 空响应 | 完整 rollback | P0 |
| TC-CTX-006 | 缺 API Key | 不删除消息，明确诊断 | P0 |
| TC-CTX-007 | 硬约束在压缩区 | 原文逐字保留 | P0 |
| TC-CTX-008 | 最新用户消息 | 恰好一次 | P0 |
| TC-CTX-009 | Tool call/result | Pair 合法 | P0 |
| TC-CTX-010 | Secret in Tool Result | 外发内容脱敏 | P0 |
| TC-CTX-011 | 输出 Token 不降 | rollback | P1 |
| TC-CTX-012 | 输入对象 | 不被原地修改 | P1 |
| TC-CTX-013 | 多次压缩 | Summary 状态不污染新 Session | P0 |
| TC-CTX-014 | 随机消息序列 | Property invariants 成立 | P0 |

建议使用 Hypothesis 生成 role、tool call 和边界组合。

## 5.5 Tool Contract

对每个 Tool 自动执行：

1. 从 Pydantic Model 生成 JSON Schema；
2. 生成最小合法 payload；
3. 通过 Tool Handler 调用；
4. API 返回非 422；
5. 响应满足统一 envelope。

| ID | Tool |
|---|---|
| TC-CONTRACT-001 | plan_create |
| TC-CONTRACT-002 | plan_update_step |
| TC-CONTRACT-003 | plan_cascade |
| TC-CONTRACT-004 | plan_status |
| TC-CONTRACT-005 | memory_classify/tag |
| TC-CONTRACT-006 | memory_store（目标） |
| TC-CONTRACT-007 | memory_query |
| TC-CONTRACT-008 | memory_filter |
| TC-CONTRACT-009 | checkpoint_create |
| TC-CONTRACT-010 | checkpoint_review |

## 5.6 Plan

| ID | 用例 | 期望 |
|---|---|---|
| TC-PLAN-001 | Create Plan | Plan + Steps 单事务成功 |
| TC-PLAN-002 | 空任务 | 422 |
| TC-PLAN-003 | 自依赖 | conflict |
| TC-PLAN-004 | 不存在依赖 | conflict |
| TC-PLAN-005 | 跨 Plan 依赖 | conflict |
| TC-PLAN-006 | 创建环 | conflict |
| TC-PLAN-007 | 更新形成环 | rollback |
| TC-PLAN-008 | 非法状态转换 | conflict |
| TC-PLAN-009 | Cascade strong/moderate/weak | 影响正确 |
| TC-PLAN-010 | 并发更新 | 无半状态 |

## 5.7 Memory

| ID | 用例 | 期望 |
|---|---|---|
| TC-MEM-001 | Classify constraint | 正确层级和 evidence |
| TC-MEM-002 | 无匹配 | 明确 unknown/default，不伪造高置信 |
| TC-MEM-003 | Store 同内容两次 | 一条记录 |
| TC-MEM-004 | 同内容不同来源 | 按产品规则处理 |
| TC-MEM-005 | Import 重启三次 | 条目数不增加 |
| TC-MEM-006 | 文件变更 | 更新或新版本，不重复旧数据 |
| TC-MEM-007 | λ 边界 0.3/0.4/0.7/0.8 | 无未定义区间 |
| TC-MEM-008 | Query tags + layer | 交集正确 |
| TC-MEM-009 | Delete by source | 仅删除目标数据 |
| TC-MEM-010 | 10k 数据 | 满足性能目标 |

## 5.8 Checkpoint

| ID | 用例 | 期望 |
|---|---|---|
| TC-CP-001 | 合法 Plan 快照 | 成功 |
| TC-CP-002 | Plan 不存在 | 404/validation error |
| TC-CP-003 | completed ID 不属于 Plan | conflict |
| TC-CP-004 | 并发编号 | 不重复 |
| TC-CP-005 | 相同规则重复 Review | 幂等 |
| TC-CP-006 | Chain | 按编号升序 |

## 5.9 Server 与安全

| ID | 用例 | 期望 |
|---|---|---|
| TC-SERVER-001 | `python -m harness_server` | READY |
| TC-SERVER-002 | `/health` | 200，不暴露绝对路径 |
| TC-SERVER-003 | `/ready` DB 失败 | 非 ready |
| TC-SERVER-004 | 重复启动 | 复用/拒绝，不双进程 |
| TC-SERVER-005 | 非 loopback 未授权 | 拒绝 |
| TC-SEC-001 | Secret redaction | 外发和日志无 Secret |
| TC-SEC-002 | 超长输入 | 422 |
| TC-SEC-003 | SQL injection payload | 数据不受影响 |
| TC-SEC-004 | Uninstall path traversal | 拒绝 |

## 6. 当前新增回归测试

### `tests/test_context_integrity_regressions.py`

- Merge 分支尾消息重复；
- Summary 失败保留原始消息；
- 硬约束逐字保留。

### `tests/test_release_readiness_regressions.py`

- Session 约束隔离；
- 审计格式兼容；
- Memory Filter Tool/API 契约；
- Checkpoint Tool required fields；
- Plan Status Schema；
- 安装 Server runtime；
- OpenAI Runtime 依赖；
- 版本一致性；
- Memory 幂等；
- Loopback 和 SQL 字段白名单安全基线。

当前已确认缺陷采用 strict xfail，目的不是忽略缺陷，而是把它们固定为 Release Blocker，并避免文档/测试提交本身破坏现有基线。修复缺陷后必须删除对应 xfail。

## 7. CI 方案

当前 `develop` CI：

```bash
pip install -e ".[dev,mcp]"
pytest -ra --junitxml=test-results/pytest-<python>.xml
```

Matrix：Python 3.10/3.11/3.12，`fail-fast: false`，每个版本上传 JUnit Artifact。

### 后续必须增加

```bash
ruff check .
ruff format --check .
mypy plugins mcp
shellcheck scripts/*.sh crons/*.sh
pytest --cov --cov-fail-under=85
pip-audit
```

覆盖率阈值不能替代 E2E Release Gate。

## 8. 缺陷管理

- P0：必须有测试，修复前阻断 Beta；
- P1：必须有测试或明确的手工复现步骤；
- strict xfail 必须包含原因和对应 Review ID；
- 修复后 XPASS 会使 CI 失败，要求移除 xfail；
- 不允许永久 xfail；
- Flaky test 必须记录根因，不能简单重试掩盖。

## 9. 退出标准

### Beta 测试退出标准

- P0 用例 100% 通过；
- Contract 100% 通过；
- Python Matrix 100% 通过；
- Install E2E 100% 通过；
- Context Property Test 100% 通过；
- 无访问真实 HOME；
- 无未披露外部 API 调用；
- Known Limitations 已更新。

### Stable 测试退出标准

- Beta 标准全部满足；
- Linux/macOS 完整 E2E；
- Hermes 真实版本兼容测试；
- 14 天 soak test 无数据完整性 P0；
- 依赖安全扫描无 High/Critical；
- 外部用户安装反馈通过。

## 10. 测试报告格式

每次 Release Candidate 报告必须包含：

- Commit SHA；
- 环境 Matrix；
- 总用例、通过、失败、XFAIL、跳过；
- P0/P1 缺陷；
- 未执行项和原因；
- Release 建议；
- JUnit/日志位置；
- 与上一版本差异。

当前执行结果见 `docs/testing/TEST_REPORT_2026-07-27.md`。
