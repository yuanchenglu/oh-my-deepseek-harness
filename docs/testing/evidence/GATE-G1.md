# GATE-G1 Evidence：制品与 Runtime 就绪

- Gate：`G1`
- 最终状态：**PASS**
- Checklist：**10 PASS / 0 FAIL / 0 BLOCKED**
- 初始评估 PR：#77（Merged）
- 初始评估结论：FAIL（8 PASS / 2 FAIL）
- 初始评估 Squash：`9a8c3a8f7b94111d626ec9319612e0574de04c84`
- Remediation Work ID：`QA-ART-001` / Issue #25
- Remediation PR：#78（Merged）
- Remediation Squash：`5ebb3a0c9b44cd5f2a2be789f9224740d47894f8`
- PASS 复评 PR：#79（Merged）
- PASS 复评基线：`develop@5ebb3a0c9b44cd5f2a2be789f9224740d47894f8`
- Final PR Head：`e6e39b54040c5deba12d474daf596f7da4272a7c`
- Final Required CI：Run #193 / ID `30384094675`
- PASS Squash Commit：`b0b9d2e0337a9f40f2abcdb0f91ce8b2865ea765`
- 最终 `develop`：`b0b9d2e0337a9f40f2abcdb0f91ce8b2865ea765`
- `master`：`398701c5cf6495180a7a7566f09921cf126a054a`
- 评估日期：2026-07-29

> G1 是独立 Gate，不由 M1 8/8 Complete 或单次绿色 CI 自动推导。初评发现的 sdist 与 twine 缺口已由 canonical owner `QA-ART-001` 完整闭环；最终复评与同一 PR Head Required CI 均通过。

## 1. 审计轨迹

| 阶段 | PR / Commit | CI | 结论 |
|---|---|---|---|
| 初始 G1 评估 | PR #77 / `9a8c3a8f` | Run #178 / `30381652033` | FAIL：缺 sdist、缺 twine check |
| QA-ART-001 remediation | PR #78 / `5ebb3a0c` | Run #184 / `30382668758` | Complete |
| G1 PASS 复评 | PR #79 / `b0b9d2e0` | Run #193 / `30384094675` | PASS |

Run #191 / ID `30383573466` 曾因主计划遗漏固定 Hermes 候选标识 `v0.19.0` / `v2026.7.20` 触发静态契约失败；恢复规范标识后，Run #192 与最终 Run #193 均在 Python 3.10、3.11、3.12 全绿。未修改测试或业务代码规避失败。

## 2. M1 闭环

| Work ID | Issue | Delivery | 状态 |
|---|---:|---|---|
| `PKG-001` | #18 | PR #62 · `2098dffc` | Complete |
| `PKG-002` | #19 | PR #63 · `ae277d1d` | Complete |
| `RUN-001` | #20 | PR #64 · `31366ceb` | Complete |
| `RUN-002` | #21 | PR #65 · `f1c04697` | Complete |
| `INS-001` | #22 | PR #68 · `2e5438a7` | Complete |
| `INS-002` | #23 | PR #70 · `d1d3269d` | Complete |
| `INS-003` | #24 | PR #72 · `9e5295ac` | Complete |
| `QA-ART-001` | #25 | PR #74 · `7adbb0cb`; remediation PR #78 · `5ebb3a0c` | Complete |

QA remediation code-acceptance Run #183 / ID `30382373294`：Python 3.10、3.11、3.12 每版本 231 tests、0 failures、0 errors、9 strict XFAIL；artifact JUnit 每版本 1 test、0 failures、0 errors、0 skipped。

## 3. 原始 G1 条款

| # | 要求 | 证据 | 判定 |
|---:|---|---|---|
| 1 | clean source 构建 wheel + sdist | 同一 `git archive HEAD` snapshot 构建唯一 wheel 与 sdist；记录 SHA256 与 inventory | PASS |
| 2 | `python -m twine check dist/*` | Run #183/#184 三版本对 wheel、sdist 均 PASSED | PASS |
| 3 | wheel package data 完整 | wheel 39 files；sdist 75 files；Server/Plugin/Context/YAML/config 完整 | PASS |
| 4 | 源码目录外导入公共 package | fresh non-editable venv、空 `PYTHONPATH`、仓库外 cwd | PASS |
| 5 | 不依赖源码 symlink/相对路径 | module origin、sys.path、archived-source exclusion 全通过 | PASS |
| 6 | Console Script 启动/检查/停止 Server | install、status/Doctor、smoke、upgrade、uninstall/stop 全通过 | PASS |
| 7 | `/health`、`/ready`、`/version` 契约 | final-wheel smoke 返回 200、ready、`3.0.0b1` | PASS |
| 8 | 空 HOME 完整生命周期 | pip install → install → doctor → smoke → uninstall → pip uninstall | PASS |
| 9 | 重复安装/端口/中断/保留数据 | INS-001–003 Required CI | PASS |
| 10 | 不访问真实 `~/.hermes` | 临时 HOME/data/DB/memory/port/fake Secret | PASS |

## 4. 安全边界

| 风险 | 结论 |
|---|---|
| 真实 HOME / DB / Memory 污染 | PASS |
| Secret 泄露 | PASS |
| foreign PID / PID reuse | PASS |
| symlink / traversal | PASS |
| destructive operation confirmation | PASS |
| rollback / interrupted lifecycle | PASS |

## 5. 支持分层与 exclusions

- 固定 Hermes 候选：Hermes Agent v0.19.0 / Git tag `v2026.7.20`；
- Python 3.10：package/core/artifact lifecycle，以及完整 Hermes 组合的预期拒绝；
- Python 3.11–3.12：完整 Hermes 候选组合；
- real Hermes E2E 属于 `COMPAT-001` / M4 / G3；
- byte-for-byte reproducibility、SBOM、provenance 属于 `REL-006`；
- 当前 Runtime 仍为 9 Tools，目标 10；
- 当前 9 个 strict XFAIL 均有 canonical owner，不属于无主豁免。

## 6. Gate 结论

**G1 PASS。**

G1 PASS 仅解锁 M2，不表示 Public Beta、master、Tag、GitHub Release、PyPI、real Hermes compatibility、Migration、Security、SBOM、reproducibility 或 Stable Ready。

M2 当前串行唯一任务：`CTX-001` #26。后续顺序：

```text
CTX-001 → CTX-002 → CTX-003 → CTX-004 → SES-001 → PRIV-001 → G2
```
