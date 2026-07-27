# 测试报告：oh-my-deepseek-harness

- 测试日期：2026-07-27
- 测试分支：`develop`
- 测试 Commit：`9d0cea1919006bc027b3c47127747f9d4094e065`
- Draft PR：#1 `develop → master`
- GitHub Actions Workflow：CI Run #23
- Run ID：`30257747874`
- 运行环境：Ubuntu 24.04 / Python 3.10、3.11、3.12
- 测试命令：`pytest -ra --junitxml=test-results/pytest-<python>.xml`

## 1. 执行结论

GitHub Actions 三个 Python Matrix Job 全部成功完成：

- 依赖安装：通过；
- 完整 pytest：通过；
- JUnit Artifact 上传：通过。

但这不代表项目达到发布条件。测试中有 **12 个 strict XFAIL**，对应 Code Review 已确认、尚未修复的 P0/P1 缺陷。CI 绿色的含义是：

1. 现有 144 个行为测试通过；
2. 12 个已知缺陷能够稳定复现；
3. 没有出现未预期失败；
4. 当前版本仍然不应发布 Stable，也不满足 Beta Release Gate。

## 2. 测试统计

| Python | Total | Passed | Failed | Errors | XFAIL/Skipped | Duration | Job |
|---|---:|---:|---:|---:|---:|---:|---|
| 3.10 | 156 | 144 | 0 | 0 | 12 | 1.198s | Success |
| 3.11 | 156 | 144 | 0 | 0 | 12 | 0.837s | Success |
| 3.12 | 156 | 144 | 0 | 0 | 12 | 0.940s | Success |

Matrix 聚合：

- 总执行记录：468；
- Passed：432；
- Known XFAIL：36（同 12 个用例在 3 个 Python 版本执行）；
- Unexpected Failure：0；
- Unexpected Error：0；
- XPASS：0。

## 3. 首轮执行与测试校正

### CI Run #19

首轮执行结果：

- Total：156；
- Passed：144；
- XFAIL：11；
- Failure：1；
- 三个 Python Job 均失败。

失败原因为 `test_merge_path_does_not_duplicate_tail_messages` 出现 `XPASS(strict)`。分析后确认不是业务缺陷已修复，而是测试边界仍从 `compress_start=1` 开始，没有进入目标 `_merge=True` 分支。

只修改测试夹具，固定：

- `compress_start=2`；
- `compress_end=4`；
- 使 Summary Role 与第一条 Tail Role 冲突；
- 强制覆盖 Merge Assembly 分支。

没有修改任何业务实现。修正后的 CI Run #23 三个 Job 全部成功，目标缺陷按预期 XFAIL。

## 4. 通过能力

以下现有测试和新增安全基线测试通过：

- 当前仓库原有 142 个测试；
- Harness Server 基础端点测试；
- Tool 注册数量、名称、Schema 和 Handler 可调用性；
- Plan、Memory、Checkpoint 当前基础逻辑；
- Intent、Gate、Assessor、Learner 当前单元行为；
- Context Compressor 当前非目标分支行为；
- Server 默认监听 loopback；
- SQLite 动态 UPDATE 字段使用白名单。

说明：原有测试通过只证明其断言范围内的实现行为，不证明安装、真实 Hermes、真实 Server 子进程和外部 DeepSeek API 已形成端到端闭环。

## 5. 已确认 XFAIL 缺陷

## 5.1 Context Integrity

### XF-CTX-001 Merge 分支重复尾部消息

测试：`test_merge_path_does_not_duplicate_tail_messages`

期望：每条 Tail Message 恰好出现一次。

当前：Merge Assembly 会重复追加尾部消息。

严重度：P0。

### XF-CTX-002 Summary 失败丢失原始历史

测试：`test_summary_failure_preserves_original_messages`

期望：Provider 返回空、异常或超时时，完整返回原 messages。

当前：使用静态占位摘要替代压缩区原消息。

严重度：P0。

### XF-CTX-003 硬约束没有逐字保留

测试：`test_hard_constraint_message_survives_verbatim`

期望：受保护约束原文在输出中完整存在。

当前：边界调整后仍可能进入压缩切片。

严重度：P0。

## 5.2 Session 与审计

### XF-POLICY-001 跨 Session 约束污染

测试：`test_hard_constraints_are_isolated_between_sessions`

期望：Session B 不继承 Session A 约束。

当前：模块级全局 `set` 保留旧约束。

严重度：P0。

### XF-AUDIT-001 写入和解析格式不兼容

测试：`test_immune_audit_parses_assessor_output_format`

期望：Assessor 生成的记录可被 Audit 读取。

当前：写入多行 Markdown，解析器只支持单行管道格式。

严重度：P1。

## 5.3 Tool Contract

### XF-CONTRACT-001 Memory Filter 参数名不一致

测试：`test_memory_filter_tool_uses_api_contract`

期望：Tool Handler 发送 API 接收的 `lambda`。

当前：发送 `lambda_value`。

严重度：P1。

### XF-CONTRACT-002 Checkpoint Tool 缺少必填字段

测试：`test_checkpoint_tool_schema_matches_api_required_fields`

期望：Tool Schema 声明 `plan_id`、`plan_steps`、`completed_step_ids`。

当前：只声明 `plan_id` 必填。

严重度：P1。

### XF-CONTRACT-003 Plan Status Schema 不匹配

测试：`test_plan_status_schema_matches_service_enum`

期望：Schema enum 与 `PlanStatus` 一致。

当前：无 enum 且描述包含服务不支持的 `blocked`。

严重度：P1。

## 5.4 安装与依赖

### XF-INSTALL-001 安装脚本不安装 Harness Server

测试：`test_install_script_installs_harness_server_runtime`

期望：安装脚本安装或复制 Server Runtime。

当前：只复制两个 Plugin。

严重度：P0。

### XF-DEPS-001 缺少 OpenAI Runtime 依赖

测试：`test_runtime_dependencies_include_openai`

期望：启用 Context Engine 时依赖完整。

当前：压缩器 import `openai`，项目依赖未声明。

严重度：P0/P1，取决于 Context 是否默认启用。

### XF-RELEASE-001 版本号不一致

测试：`test_project_versions_are_consistent`

当前：Root、Harness Plugin、Context Plugin 版本不一致。

严重度：P2。

## 5.5 Memory

### XF-MEM-001 Memory 存储不幂等

测试：`test_memory_import_storage_is_idempotent`

期望：同内容、同来源重复写入只保留一条。

当前：普通 INSERT，产生重复记录。

严重度：P1。

## 6. 尚未完成的测试

以下测试因当前产品缺少可执行闭环，本次不能声称已完成：

### 6.1 真实安装 E2E

未执行：空 HOME 下 `dry-run → install → doctor → uninstall`。

原因：当前安装脚本不会安装 Harness Server 和完整依赖；没有 Doctor 和完整卸载流程。

### 6.2 真实 Harness Server 子进程 E2E

未执行：Plugin 自动启动 Server、readiness、九个 Tool 真实 HTTP 调用、停止。

原因：Server package 和进程管理链路未成立。

### 6.3 真实 Hermes 集成

未执行：明确 Hermes Release 下 Hook 注册、Context Engine 加载和 Tool 调用。

原因：CI 使用 Mock Hermes；仓库未提供可复现兼容环境。

### 6.4 真实 DeepSeek API

未执行：真实摘要质量、Token、网络超时和 API 兼容。

原因：普通 CI 不应使用真实 Secret；需要单独受控验证。

### 6.5 隐私和 Secret Redaction

未执行：当前没有 Redaction Pipeline。

### 6.6 macOS 和 Windows/WSL

本次 GitHub Actions 只运行 Ubuntu。

## 7. 测试覆盖评价

### 已具备

- 较多单元测试；
- FastAPI TestClient 基础测试；
- Python 3.10–3.12 Matrix；
- JUnit Artifacts；
- 已知缺陷可执行回归规格。

### 主要缺口

- 安装 E2E；
- 真实进程 E2E；
- Tool Contract 自动生成；
- Context Property Tests；
- 并发 Session；
- DB Migration；
- HOME 隔离；
- Secret Redaction；
- Hermes Compatibility；
- Linux/macOS Matrix；
- Ruff、类型、ShellCheck、Coverage、安全扫描。

## 8. Release 判断

| 发布类型 | 结论 | 原因 |
|---|---|---|
| Stable | **禁止发布** | 4+ P0 完整性/安装问题 |
| Public Beta | **暂不满足** | 安装、Context、Session、Contract 未关闭 |
| Experimental Preview | 可保留 | 必须明确 Known Limitations，不宣称完整可用 |

## 9. 下一测试动作

按优先顺序：

1. 修复 Context 三项 P0，将 3 个 XFAIL 转为 Pass；
2. 修复 Session 隔离；
3. Server package 化，增加 Process E2E；
4. Installer + Doctor + Uninstall E2E；
5. Tool Contract 单一源，九个 Tool 全链测试；
6. Memory import 幂等；
7. 测试临时 HOME 和 App Factory；
8. Secret Redaction；
9. Hermes/macOS 兼容测试。

## 10. 测试证据

GitHub Actions Run #23 生成三个 JUnit Artifact：

- `pytest-3.10`
- `pytest-3.11`
- `pytest-3.12`

Artifacts 由 GitHub Actions 保存，测试报告中的统计直接从 JUnit XML 读取。

## 11. 最终结论

当前测试基线可信地说明：

- 现有 144 个断言在 Python 3.10–3.12 下稳定通过；
- 12 个关键缺陷在三个 Python 版本下稳定复现；
- 没有未预期失败；
- 项目测试基础可继续用于整改；
- 产品本身仍未达到 Open-source Beta Release Gate。
