# GATE-G1 Evidence：制品与 Runtime 就绪

- Gate：`G1`
- 评估分支：`docs/gate-g1-evaluation`
- 评估基线：`develop@8260c671786aa2ea994d61e6bde09ad57992ef36`
- 发布分支基线：`master@398701c5cf6495180a7a7566f09921cf126a054a`
- 规范来源：`docs/roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md` §5 G1
- 评估日期：2026-07-29
- 结论：**FAIL**

> G1 是独立 Gate 判定，不由 M1 8/8 Complete 自动推导。本次失败仅由原始 G1 制品条款中两个未满足项触发：尚未构建/验证 sdist，且 Required 路径没有执行 `python -m twine check dist/*`。其余 Runtime、安装生命周期和隔离条款已有可追溯证据。

## 1. 远程事实复核

| 项目 | 远程事实 | 判定 |
|---|---|---|
| `develop` | `8260c671786aa2ea994d61e6bde09ad57992ef36` | 与交接基线一致 |
| `master` | `398701c5cf6495180a7a7566f09921cf126a054a` | 尚未进入本发布周期 |
| M1 | 8/8 Complete | 具备 G1 独立评估条件 |
| 当前产品成熟度 | Experimental Preview | 未达到 Public Beta |
| Tag / GitHub Release / PyPI | 均未执行；PyPI 按 `REL-005` 保持禁用 | 符合当前边界 |
| 开放 PR | #13 为早期过时自动合并工作流 PR，base 已远落后于当前 `develop` | 不作为 G1 证据或实施路径 |

## 2. M1 八个 Work ID 闭环

| Work ID | Issue | PR | Squash Commit | Final Required CI | 状态 |
|---|---:|---:|---|---|---|
| `PKG-001` | #18 | #62 | `2098dffc9f6fef8ccb5db8385e5df5080304bbdd` | Run #81 / `30324673432` | Complete |
| `PKG-002` | #19 | #63 | `ae277d1d860713ec6bca7dd1b1eabd6632cd142e` | Run #84 / `30325534641` | Complete |
| `RUN-001` | #20 | #64 | `31366ceb1cb1ff375496bed2cdaf504ac11763ae` | Run #87 / `30326673572` | Complete |
| `RUN-002` | #21 | #65 | `f1c04697fcb43e1862cf9d5d4c6ddfa465b4c44b` | Run #108 / `30330735858` | Complete |
| `INS-001` | #22 | #68 | `2e5438a724adf92a12bb6a16d40aade3f147da7f` | Run #126 / `30333921450` | Complete |
| `INS-002` | #23 | #70 | `d1d3269de389258cc988c04b682de465d2da77c7` | Run #139 / `30335805610` | Complete |
| `INS-003` | #24 | #72 | `9e5295ac7ec51e87d1051857d676cc13f478d063` | Run #154 / `30340534593` | Complete |
| `QA-ART-001` | #25 | #74 | `7adbb0cb00e781e31fee0ee5d360f52c4bdce5eb` | Run #166 / `30343118259` | Complete before Gate evaluation |

QA-ART-001 的最终 Required 矩阵在 Python 3.10、3.11、3.12 上均为：230 tests、0 failures、0 errors、9 strict XFAIL；每个 job 另有 artifact JUnit 1 test、0 failures、0 errors。

## 3. 原始 G1 条款逐项判定

| # | 原始规范要求 | 证据与实际状态 | 判定 | 残余风险 / exclusions |
|---:|---|---|---|---|
| 1 | 从干净 Git Tag 构建 wheel 和 sdist | Required 路径使用 `git archive HEAD` 从冻结 PR Head 构建并验证一个 wheel；没有构建 sdist。正式不可变 Beta Tag 按发布顺序只能在最终 `test-release` 通过后创建，因此本 Gate 将“干净 Git Tag”按当前规范解释为冻结 Commit 的 clean archive，但 sdist 仍缺失。 | **FAIL** | QA-ART-001 必须扩展为同一 clean snapshot 构建 wheel+sdist，并记录两者 SHA256/inventory。正式 Beta Tag 仍不得提前创建。 |
| 2 | `python -m twine check dist/*` 通过 | 当前 CI、`scripts/test_artifact.sh` 和 Evidence 均无 twine 检查。 | **FAIL** | QA-ART-001 必须在 Required 路径安装受约束的 `build`/`twine`，对同批 wheel+sdist 执行检查并上传日志/JUnit。 |
| 3 | wheel 包含 Server、Plugin、Context、YAML/策略和必要 package data | `PKG-001` 与 `QA-ART-001` 验证 39-file wheel；三个公共 package、CLI/Installer/Lifecycle/Supervisor 与 YAML/config resources 均存在；不含 `plugins/`、`mcp/`、`tests/` 生产副本。 | **PASS** | 仅证明 wheel 内容；sdist 内容待条款 1 remediation。 |
| 4 | 在源码目录外可导入所有公共 package | fresh non-editable venv、空 `PYTHONPATH`、仓库外 cwd；`deepseek_harness`、`deepseek_context`、`harness_server` 及生命周期模块均从临时 venv `site-packages` 导入。 | **PASS** | 无。 |
| 5 | wheel 安装后不依赖源码 symlink 或仓库相对路径 | module-origin 与 `sys.path` 防线通过；测试未使用 editable install；旧目录不作为 wheel 生产实现。 | **PASS** | 无。 |
| 6 | Console Script 可启动、检查、停止 Server | `RUN-002` 建立 `deepseek-harness server start/status/stop/restart`；`QA-ART-001` 从最终 wheel 运行 install、Doctor、Server smoke 和 uninstall。 | **PASS** | 远程/多用户 service 不属于 G1。 |
| 7 | `/health`、`/ready`、`/version` 行为满足契约 | `RUN-001`、`RUN-002` 和 QA external lifecycle 均验证 200/ready/version 语义、DB 故障隔离和脱敏。 | **PASS** | 真实 Hermes 不参与这些 Runtime 探针。 |
| 8 | 空 HOME 下完成 pip install → install → doctor → smoke → 普通 uninstall → pip uninstall | QA external lifecycle 在临时 HOME/data/DB/动态端口中完整执行；产品 CLI 不调用 pip，最终 pip uninstall 仅由 disposable test harness 执行。 | **PASS** | Python 3.10 Doctor 按支持矩阵预期退出 5；3.11/3.12 退出 0。 |
| 9 | 重复安装、端口占用、安装中断和卸载保留数据测试通过 | `INS-001` 重复安装/事务回滚；`INS-002` unmanaged port；`INS-003` interrupted recovery、ordinary uninstall、confirmed purge；全部 Required CI 通过。 | **PASS** | 完整 Beta Schema Migration 属于 `MIG-001`，不属于 G1。 |
| 10 | 安装和测试不读取或修改真实 `~/.hermes` | 所有 M1 E2E 使用临时 HOME/data/DB/port/fake secret；Doctor 只读；测试明确断言无真实 HOME 访问。 | **PASS** | 无。 |

**G1 checklist：8 PASS / 2 FAIL / 0 BLOCKED。Gate 结论必须为 FAIL。**

## 4. `CR-P0-001` 与开放 Blocker

`CR-P0-001` 的 package/runtime/installability 链路已经由 `PKG-001`、`PKG-002`、`RUN-001`、`RUN-002`、`INS-001`、`INS-002`、`INS-003` 和 `QA-ART-001` 的合并实现及 Required CI 关闭。

当前未发现仍归属于 G1 Runtime/installability 范围的开放 P0。后续开放 P0 均有 M2 canonical owner，并因 G1 未 PASS 而保持 dependency blocked：

- `CR-P0-002` → `CTX-001` #26；
- `CR-P0-003` → `CTX-002` #27；
- `CR-P0-004` → `CTX-003` #28；
- `CR-P0-005` → `SES-001` #30。

本次新发现不是产品 Runtime P0，而是 G1 artifact-evidence 缺口，canonical owner 回收到 `QA-ART-001` #25。

## 5. 九个 strict XFAIL 的 canonical ownership

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

结论：M1 没有无主 strict XFAIL；这些 XFAIL 不阻塞 G1，但必须在各自 canonical Work ID 中转为普通 Pass，禁止改 skip 或弱化断言。

## 6. Python / Hermes 支持分层

- Python 3.10：package/core、artifact lifecycle，以及对 Hermes v0.19.0 完整组合的预期拒绝；
- Python 3.11–3.12：完整 Hermes v0.19.0 候选组合；
- Python 3.10 的绿色 CI 不得描述为真实 Hermes integration E2E。

真实 Hermes discovery、enablement、Hook、ContextEngine、Tool E2E 的 canonical owner 是 `COMPAT-001` #46，依赖 `QA-002`，位于 M4/G3。把它前置为 G1 会形成 `G1 → M2 → M3 → M4/COMPAT-001 → G1` 的循环依赖，因此不属于 G1。`HERMES_MATRIX.md` 末尾“G1/G3 still require”属于过时矛盾表述，必须修正为仅 G3。

## 7. Artifact hash、reproducibility 与 provenance

三个 Python job 独立构建的 wheel SHA256 不同。原始 G1 条款只要求能够从 clean snapshot 构建、检查、安装和运行，并未要求 byte-for-byte reproducibility。

因此：

- wheel hash 差异不是本次 G1 的失败原因；
- `REL-006` 仍负责 RC/final artifact reproducibility、SBOM、provenance 和精确 master Commit 重建；
- 本次 remediation 只补齐同一 snapshot 的 sdist 与 `twine check`，不得提前宣称 reproducible build PASS。

## 8. 安全边界复核

| 风险 | 证据 | 判定 |
|---|---|---|
| 真实 HOME / DB / Memory 污染 | 临时 HOME/data/DB/memory root；import/Doctor no-write tests | PASS |
| Secret 泄露 | fake Secret 不出现在上传文本；Doctor/log/output redaction | PASS |
| foreign PID / PID reuse | PID + start token + exact argv + instance ID；no-signal fixtures | PASS |
| symlink / traversal | install conflict、purge root、manifest、external DB symlink fail-closed | PASS |
| destructive operation | `--confirm` before mutation；ordinary uninstall preserves user data | PASS |
| rollback / interrupted lifecycle | transaction marker、backup、recover、exit 6 evidence retention | PASS |

## 9. Gate 结论与唯一后续动作

**结论：G1 FAIL。**

失败条款：

1. clean snapshot 尚未构建和验证 sdist；
2. Required 路径尚未执行 `python -m twine check dist/*`。

唯一合法 remediation：

1. 重新打开 canonical Issue #25（QA-ART-001）；
2. 在独立分支扩展 `scripts/test_artifact.sh`、package artifact tests、CI dependencies 和 Evidence；
3. 同一 clean snapshot 构建 wheel+sdist，执行 twine check，记录 SHA256/inventory；
4. 在 Python 3.10/3.11/3.12 Required jobs 上保持完整 external lifecycle；
5. 合并 remediation 后重新建立独立 G1 评估；
6. G1 PASS 前不得启动 CTX-001、SES-001 或其他 M2 Work ID。

## 10. 明确 exclusions

本 Gate 不声明：

- Public Beta、master、Tag、GitHub Release 或 PyPI publication ready；
- byte-for-byte reproducible build、SBOM 或 provenance；
- 真实 Hermes E2E；
- Context、Session、Privacy、Tool Contract、Memory、Plan、Checkpoint、Audit、Migration 或 Security 已完成；
- 当前 Runtime 已达到目标 10 Tools（仍为 9）。
