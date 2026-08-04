# 升级（UPGRADE）

升级通过 `deepseek-harness upgrade` 完成。正式升级**先备份、显式迁移，任一步失败自动回滚到可运行旧版本**。

## 1. 预览（不写任何东西）

先运行 `--dry-run`，报告 Config/DB/JSONL/进程迁移影响，不产生任何持久化变化：

```bash
deepseek-harness upgrade --dry-run
```

## 2. 正式升级

```bash
deepseek-harness upgrade
```

升级事务：
- 备份当前部署（Config、DB、JSONL 事件、runtime state）到 `<data-root>/backups`；
- 显式执行迁移；
- 任一步失败时自动回滚到可运行的旧版本。

## 3. 中断恢复

若升级事务被中断（如进程被杀、网络断了），先恢复事务再继续：

```bash
deepseek-harness recover
```

## 4. 验证

```bash
deepseek-harness doctor
```

## 5. 失败处理

- 升级失败自动回滚后，`doctor` 仍应报告旧版本可运行。
- 若 `recover` 提示事务不完整，保留 `<data-root>/backups` 与事务标记，不要手动删除，详见[排障](TROUBLESHOOTING.md)。