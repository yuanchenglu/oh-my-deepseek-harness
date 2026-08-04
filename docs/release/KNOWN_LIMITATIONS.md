# Known Limitations（已知限制）

> 本文件列出 `oh-my-deepseek-harness` 当前已知的限制与边界。任何限制不得被文档或 README 掩盖。能力状态与证据见 [能力矩阵](../capabilities/CAPABILITY_MATRIX.md)。

## 1. 版本与平台

- **Python 3.10**：仅包级/纯模块 CI 验证；不是 Hermes v0.19.0 的完整集成环境。Doctor 在 3.10 上可能返回 `5`（unsupported）。
- **完整集成环境**：Python 3.11/3.12 + Linux/macOS + Hermes v0.19.0（tag `v2026.7.20`）。
- **PyPI**：保持禁用；如需安装使用本地 wheel 或源码构建。

## 2. 尚未完成的能力（Experimental / Beta）

| 能力 | 状态 | 说明 |
|------|------|------|
| 完整 Hermes 集成 | Beta | 真实 Hermes E2E 由 `COMPAT-001` 验证，完成前不得标 Stable |
| `memory_store` | Experimental | Schema/Contract 已定、领域逻辑已实现，但 handler 未注册为运行时 Tool |
| 会话学习 | Experimental | 仅记录 Session 结束 + 超 10 轮输出 Skill 候选日志；**不自动创建 Skill** |
| 推理强度路由 | Degraded | 受 API Hook 协议限制，降级为上下文提示注入 |
| 时效信息注入 | Degraded | API 拒绝 `role=latest_reminder`，降级为上下文文本注入 |

## 3. 安全与信任边界

- **本地 API**：Beta 仅承诺 loopback（`127.0.0.1`）本地 API，不提供远程访问安全承诺。
- **外发 Summary**：默认关闭；明确启用后才外发，且默认脱敏、不发送完整 Tool 参数。
- **日志隐私**：默认不记录完整 Prompt、API Key、Tool Result 与 Memory 原文。
- **密钥**：仅通过环境变量注入（如 `DEEPSEEK_API_KEY`）；Doctor 从不打印密钥值。

## 4. 生命周期边界

- **URL 校验**：安装/升级要求 `HARNESS_DATA_ROOT` 为规范路径；拒绝通过 symlink 的 `.hermes` 目录执行清除。
- **清除**：`uninstall --purge-data --confirm` 仅删除规范化数据根内的已知路径；未知顶层路径会被拒绝。
- **升级回滚**：任一步失败自动回滚；`recover` 用于恢复中断事务。

## 5. 外部依赖

- 部分功能需要 `rsync`、`sqlite3` CLI、`pyyaml`（非必需）。
- Summary 请求发送到外部 Provider 后，其数据保留由 Provider 政策决定，需自行确认。

## 历史

已知缺陷的修复遵循 FR-QA-008：有 Issue、精确复现与 strict XFAIL；修复后删除 XFAIL。当前 **XFAIL 全清（0）**。