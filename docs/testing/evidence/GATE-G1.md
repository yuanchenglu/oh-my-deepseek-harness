# GATE-G1 Evidence：制品与 Runtime 就绪

- Gate：`G1`
- 初始评估 PR：#77（Merged）
- 初始评估 Squash：`9a8c3a8f7b94111d626ec9319612e0574de04c84`
- 初始结论：**FAIL — 8 PASS / 2 FAIL / 0 BLOCKED**
- Remediation Work ID：`QA-ART-001` / Issue #25
- Remediation PR：#78（Merged）
- Remediation Squash：`5ebb3a0c9b44cd5f2a2be789f9224740d47894f8`
- 复评分支：`docs/gate-g1-pass-re-evaluation`
- 复评基线：`develop@5ebb3a0c9b44cd5f2a2be789f9224740d47894f8`
- 发布分支基线：`master@398701c5cf6495180a7a7566f09921cf126a054a`
- 规范来源：`docs/roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md` §5 G1
- 评估日期：2026-07-29
- 复评结论：**PASS**

> G1 由原始十条 Gate 条款独立判定，不由 M1 8/8 Complete 或单次绿色 CI 自动推导。初评发现的 sdist 与 twine 两个缺口已由 canonical owner `QA-ART-001` 在 PR #78 闭环；复评结果为 10 PASS / 0 FAIL / 0 BLOCKED。

## 1. 远程事实复核

| 项目 | 远程事实 | 判定 |
|---|---|---|
| `develop` | `5ebb3a0c9b44cd5f2a2be789f9224740d47894f8` | QA remediation 已合入 |
| `master` | `398701c5cf6495180a7a7566f09921cf126a054a` | 尚未进入本发布周期 |
| M1 | 8/8 Complete | 全部 canonical Issues 已关闭 |
| G1 初评 | PR #77 / `9a8c3a8f...` | FAIL，证据保留 |
| QA remediation | PR #78 / `5ebb3a0c...` | Complete |
| 当前产品成熟度 | Experimental Preview | G1 PASS 不等于 Public Beta |
| Tag / GitHub Release / PyPI | 均未执行；PyPI 按 `REL-005` 禁用 | 符合阶段边界 |
| 历史开放 PR #13 | 早期过时自动合并工作流 PR | 不属于当前发布链路 |

## 2. M1 八个 Work ID 闭环

| Work ID | Issue | Delivery | Final Required CI | 状态 |
|---|---:|---|---|---|
| `PKG-001` | #18 | PR #62 · `2098dffc` | Run #81 / `30324673432` | Complete |
| `PKG-002` | #19 | PR #63 · `ae277d1d` | Run #84 / `30325534641` | Complete |
| `RUN-001` | #20 | PR #64 · `31366ceb` | Run #87 / `30326673572` | Complete |
| `RUN-002` | #21 | PR #65 · `f1c04697` | Run #108 / `30330735858` | Complete |
| `INS-001` | #22 | PR #68 · `2e5438a7` | Run #126 / `30333921450` | Complete |
| `INS-002` | #23 | PR #70 · `d1d3269d` | Run #139 / `30335805610` | Complete |
| `INS-003` | #24 | PR #72 · `9e5295ac` | Run #154 / `30340534593` | Complete |
| `QA-ART-001` | #25 | PR #74 · `7adbb0cb`; remediation PR #78 · `5ebb3a0c` | Run #184 / `30382668758` | Complete |

QA remediation 代码验收 Run #183 / ID `30382373294` 在 Python 3.10、3.11、3.12 上均为：231 tests、0 failures、0 errors、9 strict XFAIL；每个 job 另含 artifact JUnit 1 test、0 failures、0 errors、0 skipped。最终 PR Head Run #184 三版本全部成功。

## 3. 原始 G1 条款逐项复评

| # | 原始规范要求 | 复评证据 | 判定 | 残余风险 / exclusions |
|---:|---|---|---|---|
| 1 | 从干净 Git Tag 构建 wheel 和 sdist | PR #78 从同一冻结 `git archive HEAD` clean snapshot 使用 `python -m build --wheel --sdist` 构建唯一 wheel 与 sdist；三版本均记录 SHA256 和 inventory。正式不可变 Beta Tag 只能在精确 master final artifact/test-release 后创建，故当前以冻结 Commit clean archive 满足 G1 clean-source 语义。 | **PASS** | 不提前创建 Beta Tag；最终 Tag identity 属于 G3/BETA-001。 |
| 2 | `python -m twine check dist/*` 通过 | Run #183/#184 的每个 Required job 均执行 twine check，wheel 与 sdist 均 PASSED，并上传 `twine-check.log`。 | **PASS** | PyPI upload 仍禁用。 |
| 3 | wheel 包含 Server、Plugin、Context、YAML/策略和必要 package data | wheel inventory 固定为 39 files；三公共 package、CLI/Installer/Lifecycle/Supervisor 和 YAML/config 均存在；无 `plugins/`、`mcp/`、`tests/` 生产副本。sdist inventory 为 75 files，单根目录且有路径安全断言。 | **PASS** | byte-for-byte reproducibility 不属于 G1。 |
| 4 | 在源码目录外可导入所有公共 package | fresh non-editable venv、空 `PYTHONPATH`、仓库外 cwd；所有公共模块来自临时 venv `site-packages`。 | **PASS** | 无。 |
| 5 | wheel 安装后不依赖源码 symlink 或仓库相对路径 | module origin、`sys.path`、archived-source exclusion 和 no-editable assertions 全部通过。 | **PASS** | 无。 |
| 6 | Console Script 可启动、检查、停止 Server | `RUN-002` 与 artifact lifecycle 验证 install 启动、status/Doctor、smoke、upgrade 和 uninstall/stop。 | **PASS** | 远程多用户服务不属于 G1。 |
| 7 | `/health`、`/ready`、`/version` 行为满足契约 | App Factory、Supervisor 和 final-wheel smoke 均验证 200、ready 与 `3.0.0b1`。 | **PASS** | 真实 Hermes 不参与这些 Runtime probes。 |
| 8 | 空 HOME 下完成 pip install → install → doctor → smoke → 普通 uninstall → pip uninstall | 临时 HOME/data/DB/port/venv 完整执行；产品 CLI 不调用 pip；最终 pip uninstall 仅在 disposable test harness 中执行。 | **PASS** | Python 3.10 Doctor 预期退出 5；3.11/3.12 退出 0。 |
| 9 | 重复安装、端口占用、安装中断和卸载保留数据测试通过 | `INS-001`、`INS-002`、`INS-003` 的 transaction、unmanaged port、recovery、ordinary uninstall、confirmed purge Required CI 均通过。 | **PASS** | Beta Schema Migration 属于 `MIG-001`。 |
| 10 | 安装和测试不读取或修改真实 `~/.hermes` | 所有 M1 E2E 使用临时 HOME/data/DB/memory/port/fake Secret；Doctor 只读；上传文本无 fake Secret。 | **PASS** | 无。 |

**G1 checklist：10 PASS / 0 FAIL / 0 BLOCKED。Gate 结论：PASS。**

## 4. 初始失败与 remediation 审计轨迹

### 初始评估

- PR #77；
- Head `99dba726ff8b662057f485de0f981ec68b78c7e3`；
- Final CI Run #178 / ID `30381652033`；
- Squash `9a8c3a8f7b94111d626ec9319612e0574de04c84`；
- 结论：缺 sdist、缺 twine check。

Run #177 曾因 Traceability 缺少 48 个 canonical Issue URL 而三版本失败；恢复机器契约后 Run #178 全绿。Python 3.10 同轮出现一次未复现的 Supervisor startup race，Run #178、#183、#184 均通过，未通过 skip 或弱化断言处理。

### Remediation

- Issue #25 reopened 后按 canonical ownership 修复；
- TDD Head `5d93f03c5818e31761ac2958ac8590c0a36f0059`；
- Run #182 暴露 Python 3.12 no-isolation 环境缺少 `setuptools.build_meta`；
- 通过显式约束 `setuptools`/`wheel` build backend 依赖修复；
- 代码验收 Run #183 三版本全绿；
- Final PR Head `531aa0e3fd327dc9a096668432ebd1d0b2bff43b`；
- Final CI Run #184 / ID `30382668758` 三版本全绿；
- PR #78 Squash `5ebb3a0c9b44cd5f2a2be789f9224740d47894f8`；
- Issue #25 closed / completed。

## 5. `CR-P0-001` 与后续 P0

`CR-P0-001` 的 package/runtime/installability 链路已由 M1 八个 Work ID 与 artifact remediation 完整关闭。当前 G1 范围内 P0 = 0。

后续 P0 已有 canonical M2 owners：

- `CR-P0-002` → `CTX-001` #26；
- `CR-P0-003` → `CTX-002` #27；
- `CR-P0-004` → `CTX-003` #28；
- `CR-P0-005` → `SES-001` #30。

G1 PASS 解锁这些任务的阶段依赖，但不表示其缺陷已关闭。

## 6. 九个 strict XFAIL 的 canonical ownership

| XFAIL / 测试 | Canonical owner | Gate 归属 |
|---|---|---|
| Merge path 重复尾消息 | `CTX-001` #26 | G2 |
| Summary failure 不保留原消息 | `CTX-002` #27 | G2 |
| 硬约束未逐字保留 | `CTX-003` #28 | G2 |
| Session 硬约束全局污染 | `SES-001` #30 | G2 |
| assessor/audit 格式不一致 | `AUD-001` #39 | M3/G3 |
| `memory_filter` Tool/API 参数不一致 | `CON-001` #32 | M3/G3 |
| `checkpoint_create` schema 缺必填字段 | `CON-001` #32 | M3/G3 |
| Plan status schema/service enum 不一致 | `CON-001` #32 | M3/G3 |
| Memory import 非幂等 | `MEM-002` #34 | M3/G3 |

M1/G1 没有无主 strict XFAIL。后续 Work ID 必须逐项转为普通 Pass，禁止改 skip、隐藏 XPASS 或弱化断言。

## 7. Python / Hermes 支持分层

- Python 3.10：package/core/artifact lifecycle，以及对 Hermes v0.19.0 完整组合的预期拒绝；
- Python 3.11–3.12：完整 Hermes v0.19.0 候选组合；
- Python 3.10 绿色 CI 不得描述为真实 Hermes integration E2E；
- 真实 Hermes discovery、enablement、Hook、ContextEngine、Tool E2E 的 canonical owner 是 `COMPAT-001` #46，位于 M4/G3；不属于 G1，否则形成循环依赖。

## 8. Artifact hash、reproducibility 与 provenance

三版本独立构建的 wheel 与 sdist SHA256 不同。G1 要求 clean-source 可构建、twine 可检查、内容可审计、wheel lifecycle 可运行；不要求 byte-for-byte reproducibility。

因此：

- hash 差异不阻塞 G1；
- `REL-006` 继续负责 RC/final same-commit reproducibility、SBOM、provenance 与精确 master Commit 重建；
- 本 Gate 不宣称 reproducible build PASS。

## 9. 安全边界复核

| 风险 | 证据 | 判定 |
|---|---|---|
| 真实 HOME / DB / Memory 污染 | 临时 HOME/data/DB/memory root；import/Doctor no-write | PASS |
| Secret 泄露 | fake Secret 不出现在 artifact/log/JUnit 文本 | PASS |
| foreign PID / PID reuse | PID + start token + exact argv + instance ID；no-signal fixtures | PASS |
| symlink / traversal | install/purge/manifest/external DB fail-closed；sdist path/link assertions | PASS |
| destructive operation | `--confirm` before mutation；ordinary uninstall preserves data | PASS |
| rollback / interrupted lifecycle | transaction marker、backup、recover、failure evidence | PASS |

## 10. Gate 结论与下一步

**结论：G1 PASS。**

G1 PASS 仅表示 M1 artifact、Runtime、install lifecycle 与隔离 Gate 通过。它不表示：

- M2 Context/Session/Privacy 已完成；
- Public Beta、master、Tag、GitHub Release 或 PyPI publication ready；
- real Hermes compatibility、Migration、SBOM、Security、reproducibility 或 provenance 已完成；
- Runtime 已达到目标 10 Tools（当前仍为 9）。

M2 有两个依赖已满足的入口：`CTX-001` 与 `SES-001`。为遵守单一 Work ID 串行执行，本计划按 canonical §6.4 表格和 Issue 顺序选择 **`CTX-001` #26** 作为唯一当前实施任务；`SES-001` 保持合法但排队，不并行启动。

`CTX-001` 完成后继续按强制链：`CTX-002 → CTX-003 → CTX-004`，再执行尚未完成的 `SES-001` 与 `PRIV-001`，最后独立评估 G2。
