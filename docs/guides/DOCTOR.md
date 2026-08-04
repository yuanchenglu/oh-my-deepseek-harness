# Doctor（DOCTOR）

`deepseek-harness doctor` 是**只读**环境与生命周期诊断，不产生任何持久化变化。它检查 Python、Hermes、Plugin、Context、Server `/health`/`/ready`/`/version`、DB、Provider、端口、版本与权限。

## 1. 运行 Doctor

```bash
deepseek-harness doctor
```

## 2. JSON 输出

单 JSON object 输出，便于脚本消费：

```bash
deepseek-harness doctor --json
```

## 3. 退出码

| 退出码 | 含义 |
|--------|------|
| `0` | 全部通过 |
| `1` | 有检查失败 |
| `3` | 缺少依赖（missing dependency） |
| `4` | 端口冲突（port conflict） |
| `5` | 环境不支持（unsupported） |

> 在 Python 3.10 上，Doctor 可能返回 `5`（unsupported），因为 Python 3.10 不是 Hermes v0.19.0 的完整集成环境。

## 4. 检查项

- **Python**：版本与支持范围
- **Hermes**：可执行文件与版本
- **Plugin / Context**：托管文件是否就位
- **Server**：`/health`、`/ready`、`/version` 探针
- **DB**：SQLite 数据库可访问
- **Provider**：`DEEPSEEK_API_KEY` 是否配置（**Doctor 从不打印密钥值**）
- **端口**：loopback 端口可用
- **权限**：数据根 `0700`，配置/DB/事件/日志/runtime 文件 `0600`

## 5. 运行时状态

`server status` 给出运行时状态（PID、端口、探针）：

```bash
deepseek-harness server status
```

## 6. 相关

- [安装](INSTALL.md) / [升级](UPGRADE.md) / [排障](TROUBLESHOOTING.md)