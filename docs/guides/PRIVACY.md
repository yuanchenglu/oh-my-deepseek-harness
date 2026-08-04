# 隐私（PRIVACY）

本页说明 `oh-my-deepseek-harness` 的外发、数据与本地 API 边界。**Beta 仅承诺 loopback 本地 API，不提供远程访问安全承诺。**

## 1. 外发同意（Outbound Consent）

- **Summary 默认关闭**（`summary.enabled: false`）。
- 只有展示说明并获得你的明确选择后才启用。
- 例：外发策略 `redact`（脱敏），默认不发送完整 Tool 参数。

```yaml
summary:
  enabled: false
  outbound_policy: redact
  allow_tool_arguments: false
```

## 2. 数据最小化（Data Minimization）

- 只发送摘要所需的最小内容；
- 默认不发送完整 Tool 参数；
- 日志默认不记录完整 Prompt、API Key、Tool Result 与 Memory 原文。

## 3. 本地 API（Local API）

- Server 默认监听 `127.0.0.1:8200`（loopback）；
- 仅提供本地 API；不提供远程访问安全承诺；
- 配置优先级 CLI > Environment > User Config > Package Defaults。

## 4. 数据保留

| 数据 | 范围 | 默认保留 |
|------|------|---------|
| Session Policy | Session | Session 结束清理 |
| Constraint Events | 本地用户 | 用户显式清理 |
| Plan/Memory/Checkpoint | 本地用户 | Archive/Delete |
| Runtime PID | 进程 | 停止时清理 |
| Logs | 本地用户 | 可轮转 |
| Summary 请求 | 外部 Provider | 由 Provider 政策决定 |

## 5. 文件权限

- 数据根目录 `0700`；
- 配置、DB、事件、日志与 runtime 文件 `0600`。

## 6. 敏感信息

- **不要**在本仓库的 Issue、PR、文档或示例中放置真实 token、API Key、路径或 Prompt；
- 密钥只通过环境变量（如 `DEEPSEEK_API_KEY`）注入，Doctor 从不打印密钥值。

## 7. 相关

- [安装](INSTALL.md) / [Doctor](DOCTOR.md) / [已知限制](../release/KNOWN_LIMITATIONS.md)