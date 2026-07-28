# QA-ART-001 Evidence：源码外 Wheel + sdist 制品生命周期

- Work ID：`QA-ART-001`
- Canonical Issue：#25（G1 FAIL 后 reopened；remediation PR 合并后再关闭）
- 原实施 PR：#74（Merged）
- 原 Squash Commit：`7adbb0cb00e781e31fee0ee5d360f52c4bdce5eb`
- G1 评估 PR：#77（Merged）
- G1 评估 Squash：`9a8c3a8f7b94111d626ec9319612e0574de04c84`
- Remediation PR：#78（Draft）
- Remediation 分支：`test/qa-art-001-sdist-twine-remediation`
- Remediation 基线：`develop@9a8c3a8f7b94111d626ec9319612e0574de04c84`
- TDD Head：`5d93f03c5818e31761ac2958ac8590c0a36f0059`
- 代码验收 Head：`7dbe10bef7035a5ce948fd9202c995a303c084b3`
- 代码验收 CI：Run #183 / ID `30382373294`
- 状态：**REMEDIATION CODE ACCEPTED / FINAL PR-HEAD CI PENDING**
- 日期：2026-07-29

> 原 QA-ART-001 已证明 final wheel 的源码外完整生命周期。独立 G1 评估随后发现两个 artifact-evidence 缺口：同一 clean snapshot 未构建 sdist，且 Required 路径未执行 `python -m twine check dist/*`。本 remediation 只关闭这两个缺口，不扩大产品 Runtime/domain 范围，也不提前声明 G1 PASS。

## 1. Gate 缺口与 canonical ownership

G1 PR #77 的结论：**FAIL — 8 PASS / 2 FAIL / 0 BLOCKED**。

| G1 原始条款 | 原状态 | Canonical owner | Remediation 状态 |
|---|---|---|---|
| clean snapshot 构建 wheel + sdist | 仅 wheel | `QA-ART-001` #25 | Run #183 已构建并验证两类制品 |
| `python -m twine check dist/*` | 无 Required Evidence | `QA-ART-001` #25 | Run #183 三版本 wheel/sdist 均 PASSED |

其余八条 G1 条款已在原 M1 Evidence 中 PASS，不因本 remediation 重写或豁免。

## 2. 唯一 Required Artifact 路径

```text
clean git archive of exact PR Head
  → one extracted clean source snapshot
  → python -m build --wheel --sdist --no-isolation
  → exactly one 3.0.0b1 wheel + one 3.0.0b1 sdist
  → python -m twine check dist/*
  → wheel + sdist SHA256
  → wheel + sdist inventory and path-safety assertions
  → fresh non-editable temporary venv
  → pip install <wheel>[all]
  → outside probe cwd + empty PYTHONPATH
  → import-origin verification
  → install dry-run
  → clean install + Server
  → Doctor
  → health / ready / version / memory-tag smoke
  → same-version upgrade dry-run + upgrade
  → ordinary uninstall
  → explicit test-harness pip uninstall in temporary venv
```

`scripts/test_artifact.sh` 由 `tests/test_package_artifact.py` 在每个 Required `test (3.10/3.11/3.12)` job 中执行；任何 build、twine、inventory、lifecycle 或 JUnit 失败都会使 Required job 失败。

## 3. Build 依赖与隔离选择

Remediation 增加仅用于开发/测试制品路径的依赖：

- `build>=1.2,<2`；
- `twine>=5,<7`；
- `setuptools>=64,<82`；
- `wheel>=0.43,<1`。

使用 `--no-isolation` 的原因：Required CI 已显式安装并版本约束 build backend 和 twine，构建不再隐式依赖 runner 预装状态，也避免在 artifact 子步骤中再次解析不可审计的临时 build environment。

Python 3.12 首轮暴露 runner 环境没有全局 `setuptools.build_meta`；补齐显式 backend dependencies 后，三版本一致通过。

## 4. Source contamination 与路径防线

每个版本均验证：

- build input 仅来自单一 `git archive HEAD`；
- wheel 与 sdist 来源于同一 extracted snapshot；
- 临时 venv 不使用 editable install；
- `PYTHONPATH` 为空，执行 cwd 位于 repository 和 archived source 之外；
- 公共 package、CLI、Doctor、Installer、Lifecycle 均从临时 venv `site-packages` 导入；
- wheel 不包含 `plugins/`、`mcp/`、`tests/` 生产副本；
- sdist 只有一个顶层根目录；成员不得为绝对路径、包含 `..`、symlink 或 hardlink；
- sdist 必含 `pyproject.toml`、README、三个生产 package 和必要 YAML/config；
- ordinary uninstall 后 distribution 仍可 import；只有测试脚本显式执行临时 venv pip uninstall 后 import 才失败。

## 5. Run #183 真实制品

### 5.1 Python 3.10

- pytest：231 tests / 0 failures / 0 errors / 9 strict XFAIL；
- artifact JUnit：1 / 0 failures / 0 errors / 0 skipped；
- artifact archive：ID `8697569720`；digest `sha256:13879822fc6200966ee60379b6a778c0ad26bd1cc2656b92d47fc9a792a15580`；
- wheel：39 files；SHA256 `41361ef5f6266072d11b936e2f538d9961992dd702d44498eea20fc4530c40b8`；
- sdist：75 files；SHA256 `ec62b64cd55eaaebd550fd85b2dad372f4baec87b04879d5f3c995f583d74565`；
- twine：wheel PASSED；sdist PASSED。

### 5.2 Python 3.11

- pytest：231 tests / 0 failures / 0 errors / 9 strict XFAIL；
- artifact JUnit：1 / 0 failures / 0 errors / 0 skipped；
- artifact archive：ID `8697562996`；digest `sha256:433fc8517173f2da1e65e3a7a0493423b8c57357b7150a2225397ccaa076e679`；
- wheel：39 files；SHA256 `cc6f3a3079e62f03f204cd906302e85fc9ac31fab3b035aea60b8e956d99180e`；
- sdist：75 files；SHA256 `916ad2939ef1764b5228b5331e181d8e1bb01c1ef6ff862a8b169d4998e9467a`；
- twine：wheel PASSED；sdist PASSED。

### 5.3 Python 3.12

- pytest：231 tests / 0 failures / 0 errors / 9 strict XFAIL；
- artifact JUnit：1 / 0 failures / 0 errors / 0 skipped；
- artifact archive：ID `8697566811`；digest `sha256:2349070ae9b0c64ca48c6f03c348b0197d9082a89a73d8755d6fefd9af672cbe`；
- wheel：39 files；SHA256 `6c36733a7ee2c66df193142b14d1607521077c3eee305fc3f58f9bc785740715`；
- sdist：75 files；SHA256 `51a09e73de4d3a8e3e1f4109d77bc60cecaaef1994d202423b504810b5648d34`；
- twine：wheel PASSED；sdist PASSED。

## 6. Lifecycle 证据

| 阶段 | 固定结果 |
|---|---|
| install dry-run | exit 0；data root 不存在；零持久写入 |
| clean install | packaged adapters/config/DB/runtime；一个 ready Server |
| Doctor 3.10 | exit 5；明确拒绝 Python 3.10 作为完整 Hermes v0.19.0 支持 |
| Doctor 3.11/3.12 | exit 0；fake Hermes 0.19.0 与完整已安装环境通过 |
| `/health` | 200，`status=ok` |
| `/ready` | 200，`status=ready` |
| `/version` | 200，`version=3.0.0b1` |
| `POST /memory/tag` | 200；测试内容分类为 `constraint` |
| same-version upgrade | `state=up_to_date`、`changed=false`、同一 Server PID、ready |
| ordinary uninstall | managed adapters/runtime removed；distribution/config/DB preserved |
| pip command contract | 输出精确 uninstall command；产品 CLI 不执行 pip |
| explicit pip uninstall | 仅测试脚本在临时 venv 执行；之后 product import 失败 |

上传文本中不存在 fake Secret `fake-qa-art-001-key`。

## 7. 失败与修复记录

### Run #182 / ID `30382147733`

- Python 3.11：新 wheel+sdist+twine 全链路已通过；
- Python 3.12：`setuptools.build_meta` 在 no-isolation 当前环境中不可导入；
- 根因：Python 版本 runner 预装差异，不是 package source 或 sdist 内容错误；
- 修复：将 setuptools 和 wheel 加入显式 dev/build dependencies；
- 未采用：跳过 Python 3.12、改 skip、弱化断言、移除 no-isolation 或隐藏失败。

### Run #183 / ID `30382373294`

三版本完整 Required jobs 全绿，并产生 wheel、sdist、twine log、双 inventory、双 SHA256 和 lifecycle JUnit。

## 8. DoD 判定

| 验收项 | 结果 |
|---|---|
| one clean snapshot builds wheel + sdist | PASS |
| wheel filename/version/39-file inventory/SHA256 | PASS |
| sdist filename/version/75-file inventory/path safety/SHA256 | PASS |
| `python -m twine check dist/*` | PASS |
| fresh non-editable venv installs final wheel | PASS |
| no repository/archived-source product imports | PASS |
| temporary HOME/data/DB/dynamic port/fake secret | PASS |
| install dry-run + clean install | PASS |
| Doctor support/rejection matrix | PASS |
| health/ready/version and minimal API smoke | PASS |
| idempotent same-version upgrade | PASS |
| ordinary uninstall preserves distribution and data | PASS |
| product CLI never invokes pip | PASS |
| explicit pip uninstall limited to temporary venv | PASS |
| Required Python 3.10/3.11/3.12 CI | PASS at code-acceptance Head |
| artifact/JUnit upload | PASS |
| final PR-head CI | PENDING after this Evidence commit |
| Squash Merge and Issue closure | PENDING |

## 9. Reproducibility 与 exclusions

三个 job 的 wheel 和 sdist SHA256 均不同。本 remediation 证明每个实际 artifact 可构建、可检查、内容可审计且 lifecycle 通过；不声明 byte-for-byte reproducible build。

仍由后续 canonical owners 负责：

- RC/final artifact reproducibility、SBOM、provenance：`REL-006`；
- 真实 Hermes discovery/enable/Hook/Context/Tool E2E：`COMPAT-001`；
-完整 Migration：`MIG-001`；
- G1 独立重新判定：新的 `GATE-G1.md` 评估 PR；
- master、Tag、GitHub Release 和 PyPI publication：发布阶段 Work IDs。

**当前结论：QA-ART-001 remediation 的代码验收已通过；必须等待同一最终 PR Head 的 Required CI、Squash Merge、Issue closure 和 post-merge 事实收口后，才可重新评估 G1。**
