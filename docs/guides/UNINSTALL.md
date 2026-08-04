# 卸载（UNINSTALL）

卸载通过 `deepseek-harness uninstall` 完成。**普通卸载保留 Python distribution 与你的用户数据**；只有显式的 `--purge-data --confirm` 才会删除规范化数据根内的已知路径。

## 1. 普通卸载（保留数据）

```bash
deepseek-harness uninstall
```

普通卸载：
- 停止 Server（`deepseek-harness server stop`）；
- 移除 Hermes 注册、薄适配文件与 runtime state；
- **保留** Python distribution（需要时用 `pip uninstall` 移除）；
- **保留**你的产品数据（`<data-root>` 下的 Config、DB、事件、日志）。

## 2. 确认清除（purge，删除数据）

⚠️ 破坏性操作，需二次确认。仅删除规范化数据根内的已知路径：

```bash
deepseek-harness uninstall --purge-data --confirm
```

- `--purge-data` 表示同时删除数据根；
- `--confirm` 确认这次破坏性清除；
- 缺少 `--confirm` 时，命令拒绝执行，不产生任何数据或部署变化。

## 3. 移除 Python distribution

如需彻底移除已安装的 distribution（临时环境用法，非产品 CLI 负责）：

```bash
python -m pip uninstall oh-my-deepseek-harness
```

> 普通卸载保留 distribution 是刻意的：产品 CLI 从不调用 pip 卸载自身。

## 4. 安全边界

- 清除仅限规范化数据根内的已知路径；
- 拒绝通过 symlink 的 `.hermes` 目录执行清除；
- 数据根必须是规范的 `~/.hermes/oh-my-deepseek-harness` 路径；
- 未知的顶层产品路径会被拒绝，防止误删用户文件。