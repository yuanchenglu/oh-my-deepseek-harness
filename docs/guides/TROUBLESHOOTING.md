# 排障（TROUBLESHOOTING）

本页按「发生了什么 → 组件 → 是否降级 → 恢复动作 → 日志位置」组织，帮助新用户定位与恢复。

## 1. 先跑 Doctor

任何异常，先运行只读诊断：

```bash
deepseek-harness doctor
```

- 退出码 `0` = 全部通过；`1` = 检查失败；`3` = 缺依赖；`4` = 端口冲突；`5` = 环境不支持。
- 用 `--json` 获取结构化结果。

## 2. 检查运行时状态

```bash
deepseek-harness server status
```

验证托管 PID、端口与探针是否一致。

## 3. 常见问题

### 3.1 Server 未启动 / 端口冲突

- 现象：`server status` 报错，或端口被占用。
- 组件：Harness Server。
- 是否降级：是（功能不可用，但数据仍在）。
- 恢复：
  ```bash
  deepseek-harness server restart
  deepseek-harness doctor
  ```
- 日志：见下方「日志位置」。

### 3.2 升级中断或失败

- 现象：`upgrade` 中断，或 `doctor` 报旧版本不可运行。
- 组件：Lifecycle。
- 是否降级：是（已自动回滚或需要恢复）。
- 恢复：
  ```bash
  deepseek-harness recover
  deepseek-harness doctor
  ```
- 若 `recover` 报事务不完整，**保留** `<data-root>/backups` 与事务标记，不要手动删除。

### 3.3 Provider 凭据缺失

- 现象：Doctor 报 `provider` 失败。
- 组件：Provider。
- 是否降级：功能依赖 Provider 时不可用。
- 恢复：设置 `DEEPSEEK_API_KEY` 环境变量后重跑 `doctor`。
- 注意：Doctor 从不打印密钥值。

### 3.4 环境不支持（Python 3.10）

- 现象：Doctor 返回 `5`。
- 组件：Python 运行时。
- 是否降级：是；Python 3.10 不是 Hermes v0.19.0 完整集成环境。
- 恢复：使用 Python 3.11 或 3.12。

## 4. 日志位置

- Server stdout/stderr 写入用户可访问日志（log，不丢弃）；
- 结构化日志含 timestamp、level、component、event、session_id、request_id、duration、status、error_code；
- 日志默认不记录完整 Prompt、API Key、Tool Result 与 Memory 原文；
- 默认数据根：`~/.hermes/oh-my-deepseek-harness`（可用 `HARNESS_DATA_ROOT` 覆盖）。

## 5. 修复后

修复后重跑：

```bash
deepseek-harness doctor
```

确认退出码为 `0`。

## 6. 相关

- [安装](INSTALL.md) / [升级](UPGRADE.md) / [Doctor](DOCTOR.md) / [已知限制](../release/KNOWN_LIMITATIONS.md)