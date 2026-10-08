# Release Notes - v3.0.0

**oh-my-deepseek-harness** — DeepSeek 深度优化插件（14 项物理特性全激发）

## 版本

- 版本：`v3.0.0`（首个 Stable 版本）
- 基线：G0–G5 全部 PASS；48/48 Work IDs Complete
- 产品成熟度：**Stable**
- 许可：MIT
- 支持：Hermes Agent v0.19.0（tag `v2026.7.20`）+ Python 3.11–3.12（Linux/macOS）；Python 3.10 仅包级/契约 CI

## 新特性（beta 稳定化周期累计）

### 稳定性与验证
- M0–M6 全流程收口：规格/治理 → 制品 → 上下文完整性 → 契约与数据完整性 → 兼容性/RC → Public Beta → Stable。
- v3.0.0-beta.1 观察期 ≥14 天：RC 冻结、0 失败记录、0 P0/P1。
- 三平台 × 三 Python CI 矩阵（3.10–3.12）；RC 可复现构建 + provenance + SBOM。

### 插件与运行时
- Hermes v0.19.0 插件注册探针通过：5 Hooks + 9 Runtime Tools（目标契约 10，`memory_store` 待注册）。
- 版本身份统一：distribution / plugins / runtime 均为 `3.0.0`。
- 生命周期：install/upgrade/doctor/uninstall/purge/recover 全链路 + 失败回滚。

### 安全与隐私
- 本地 API（loopback）、外发 Summary 默认关闭、日志脱敏、密钥仅环境变量注入。
- SBOM、依赖审计、许可证清单（SEC-001）；安全边界测试（SEC-002）。

## Known Limitations（诚实披露）

- **外部 Beta 验证样本未达原计划 §9.2 量级（0/N）**：经 owner 决策豁免发布，转为 post-release 持续观测。详见 `docs/release/KNOWN_LIMITATIONS.md` §6 与 `docs/testing/evidence/GATE-G4.md`。
- `memory_store` 运行时 handler 未注册（领域逻辑已实现）。
- PyPI 禁用：请从本 Release 的 wheel 资产或源码构建安装。

## 安装

```bash
# 从本 Release 下载 wheel 后：
pip install oh_my_deepseek_harness-3.0.0-py3-none-any.whl

# 或从源码（tag v3.0.0）：
pip install "oh-my-deepseek-harness @ git+https://github.com/yuanchenglu/oh-my-deepseek-harness@v3.0.0"
```

详细文档见 [README](README.md) / [README_EN](README_EN.md)。

## 回滚

不可变发布：撤回策略为发布新版本（见 `docs/release/ROLLBACK.md`），不覆盖既有 tag/制品。
