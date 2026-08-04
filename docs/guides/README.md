# 生命周期指南（Lifecycle Guides）

> 本目录是 `oh-my-deepseek-harness` 官方生命周期、隐私与排障指南。
> 所有命令均来自真实 CLI（`deepseek-harness` dispatcher）并由 CI 验证。
> 新用户无需了解源码即可完成安装、升级、卸载与排障。

## 指南索引

| 指南 | 内容 | 覆盖 FR |
|------|------|---------|
| [安装（INSTALL）](INSTALL.md) | 预览、安装、验证、幂等 | FR-INSTALL-001/002/003 |
| [升级（UPGRADE）](UPGRADE.md) | 预览、备份、迁移、失败回滚 | FR-INSTALL-004 |
| [卸载（UNINSTALL）](UNINSTALL.md) | 普通卸载、确认清除（purge） | FR-INSTALL-005 |
| [Doctor（DOCTOR）](DOCTOR.md) | 只读诊断、退出码、JSON 输出 | FR-INSTALL-006、FR-OBS-005 |
| [隐私（PRIVACY）](PRIVACY.md) | 外发同意、数据最小化、本地 API | FR-SEC-001/002/003 |
| [排障（TROUBLESHOOTING）](TROUBLESHOOTING.md) | 用户错误、日志、恢复 | FR-OBS-003/004/005 |

## 数据与隐私速览

| 数据 | 范围 | 默认保留 |
|------|------|---------|
| Session Policy | Session | Session 结束清理 |
| Constraint Events | 本地用户 | 用户显式清理 |
| Plan/Memory/Checkpoint | 本地用户 | Archive/Delete |
| Runtime PID | 进程 | 停止时清理 |
| Logs | 本地用户 | 可轮转 |
| Summary 请求 | 外部 Provider | 由 Provider 政策决定 |

已知限制与边界见 [Known Limitations](../release/KNOWN_LIMITATIONS.md)。