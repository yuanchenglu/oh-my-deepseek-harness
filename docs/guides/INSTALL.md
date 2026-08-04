# 安装（INSTALL）

`oh-my-deepseek-harness` 通过 `deepseek-harness` CLI 管理整个生命周期。安装只注册 Hermes 薄适配入口、初始化数据根、启动或验证 Server，并执行 Doctor。**CLI 从不调用 pip 安装自身。**

## 完整集成环境

- Hermes Agent v0.19.0（tag `v2026.7.20`）
- Python 3.11 或 3.12（完整集成）
- Linux 或 macOS

> Python 3.10 仍在包级/纯模块 CI 中验证，但不是 Hermes v0.19.0 的完整集成环境。

## 1. 预览（不写任何东西）

先预览，确认检测值、支持范围、部署路径、端口、外发开关、备份与缺失依赖，**不产生任何持久化变化**：

```bash
bash scripts/install.sh --dry-run
```

或（已安装 distribution 后，直接调用控制台）：

```bash
deepseek-harness install --dry-run
```

## 2. 正式安装

```bash
bash scripts/install.sh
```

安装过程：
- 备份已有的 `SOUL.md`、`MEMORY.md`、`USER.md`，**不覆盖、不删除你的任何内容**；
- 注册 Hermes 薄适配入口（`deepseek-harness` / `deepseek-context` 插件）；
- 初始化产品数据根（默认 `~/.hermes/oh-my-deepseek-harness`）；
- 启动或验证一个本地 Harness Server；
- 执行 Doctor。

## 3. 验证插件已注册

```bash
hermes plugins list | grep deepseek
```

## 4. 幂等

重复安装同一版本不会重复写配置、不会重复导入 Memory、不会创建双进程、不会删除用户文件、不会无限增长备份。再次运行 `install` 是安全的。

## 5. 默认数据根与环境变量

| 变量 | 默认值 | 作用 |
|------|--------|------|
| `HARNESS_DATA_ROOT` | `~/.hermes/oh-my-deepseek-harness` | 产品数据根 |
| `HARNESS_DB_PATH` | `<data-root>/data/harness.db` | SQLite 数据库 |
| `HARNESS_MEMORIES_DIR` | `~/.hermes/memories` | Hermes Memory 目录 |
| `HARNESS_IMPORT_MEMORIES` | `0` | 启动时是否导入 Memory（默认关闭） |
| `HARNESS_HOST` | `127.0.0.1` | Loopback 主机 |
| `HARNESS_PORT` | `8200` | 本地 Server 端口 |

配置优先级固定为 **CLI > Environment > User Config > Package Defaults**。

## 6. 完成后

运行 [Doctor](DOCTOR.md) 确认环境健康，或阅读 [升级](UPGRADE.md) / [卸载](UNINSTALL.md) / [隐私](PRIVACY.md)。