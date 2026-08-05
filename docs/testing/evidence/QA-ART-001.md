# QA-ART-001 Evidence：源码外 Wheel + sdist 制品生命周期

- Work ID：`QA-ART-001`
- Canonical Issue：#25（Closed / completed）
- 原实施 PR：#74（Merged）
- 原 Squash Commit：`7adbb0cb00e781e31fee0ee5d360f52c4bdce5eb`
- G1 初评 PR：#77（Merged）
- G1 初评 Squash：`9a8c3a8f7b94111d626ec9319612e0574de04c84`
- Remediation PR：#78（Merged）
- Remediation 分支：`test/qa-art-001-sdist-twine-remediation`
- Remediation 基线：`develop@9a8c3a8f7b94111d626ec9319612e0574de04c84`
- TDD Head：`5d93f03c5818e31761ac2958ac8590c0a36f0059`
- 代码验收 Head：`7dbe10bef7035a5ce948fd9202c995a303c084b3`
- 代码验收 CI：Run #183 / ID `30382373294`
- Final PR Head：`531aa0e3fd327dc9a096668432ebd1d0b2bff43b`
- Final PR-head CI：Run #184 / ID `30382668758`
- Remediation Squash Commit：`5ebb3a0c9b44cd5f2a2be789f9224740d47894f8`
- 状态：**COMPLETE**
- 日期：2026-07-29

> 原 QA-ART-001 已证明 final wheel 的源码外完整生命周期。独立 G1 初评发现同一 clean snapshot 缺少 sdist 与 Required twine check；PR #78 已关闭两个缺口，完成最终 Head CI、Squash Merge 与 Issue closure。本文件只证明 artifact Work ID 完成，G1 PASS 仍由独立 Gate PR #79 判定。

## 1. Gate 缺口与 canonical ownership

| G1 原始条款 | 初评状态 | Canonical owner | 最终状态 |
|---|---|---|---|
| clean snapshot 构建 wheel + sdist | 仅 wheel | `QA-ART-001` #25 | PASS |
| `python -m twine check dist/*` | 无 Required Evidence | `QA-ART-001` #25 | PASS |

初始 G1 PR #77 保留 FAIL 历史；本 remediation 不删除或改写失败事实。

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

`scripts/test_artifact.sh` 由 `tests/test_package_artifact.py` 在每个 Required `test (3.10/3.11/3.12)` job 中执行；build、twine、inventory、lifecycle 或 JUnit 任一失败都会使 Required job 失败。

## 3. Build 依赖与隔离

Remediation 增加仅用于开发/测试制品路径的约束：

- `build>=1.2,<2`；
- `twine>=5,<7`；
- `setuptools>=64,<82`；
- `wheel>=0.43,<1`。

使用 `--no-isolation`，并在 CI 当前环境中显式安装 build backend 与 twine，避免依赖不同 runner 的隐式预装状态。

## 4. Source contamination 与路径防线

每个版本均验证：

- wheel 与 sdist 仅来自同一 `git archive HEAD` snapshot；
- 临时 venv 不使用 editable install；
- `PYTHONPATH` 为空，执行 cwd 位于 repository 与 archived source 之外；
- 公共 package、CLI、Doctor、Installer、Lifecycle 全部来自临时 venv `site-packages`；
- wheel 不含 `plugins/`、`mcp/`、`tests/` 生产副本；
- sdist 只有一个顶层根目录；成员不得为绝对路径、包含 `..`、symlink 或 hardlink；
- sdist 必含 `pyproject.toml`、README、三个生产 package 与必要 YAML/config；
- ordinary uninstall 后 distribution 仍可 import；测试脚本显式 pip uninstall 后 import 才失败。

## 5. Run #183 真实制品

| Python | pytest | Wheel | Wheel SHA256 | sdist | sdist SHA256 | twine |
|---|---|---|---|---|---|---|
| 3.10 | 231 / 0 failures / 0 errors / 9 XFAIL | 39 files | `41361ef5f6266072d11b936e2f538d9961992dd702d44498eea20fc4530c40b8` | 75 files | `ec62b64cd55eaaebd550fd85b2dad372f4baec87b04879d5f3c995f583d74565` | wheel+sdist PASS |
| 3.11 | 231 / 0 failures / 0 errors / 9 XFAIL | 39 files | `cc6f3a3079e62f03f204cd906302e85fc9ac31fab3b035aea60b8e956d99180e` | 75 files | `916ad2939ef1764b5228b5331e181d8e1bb01c1ef6ff862a8b169d4998e9467a` | wheel+sdist PASS |
| 3.12 | 231 / 0 failures / 0 errors / 9 XFAIL | 39 files | `6c36733a7ee2c66df193142b14d1607521077c3eee305fc3f58f9bc785740715` | 75 files | `51a09e73de4d3a8e3e1f4109d77bc60cecaaef1994d202423b504810b5648d34` | wheel+sdist PASS |

每个 job 的 artifact JUnit：1 test / 0 failures / 0 errors / 0 skipped。

| Python | Artifact ID | Archive digest |
|---|---:|---|
| 3.10 | `8697569720` | `sha256:13879822fc6200966ee60379b6a778c0ad26bd1cc2656b92d47fc9a792a15580` |
| 3.11 | `8697562996` | `sha256:433fc8517173f2da1e65e3a7a0493423b8c57357b7150a2225397ccaa076e679` |
| 3.12 | `8697566811` | `sha256:2349070ae9b0c64ca48c6f03c348b0197d9082a89a73d8755d6fefd9af672cbe` |

## 6. Lifecycle 证据

| 阶段 | 固定结果 |
|---|---|
| install dry-run | exit 0；data root 不存在；零持久写入 |
| clean install | packaged adapters/config/DB/runtime；一个 ready Server |
| Doctor 3.10 | exit 5；明确拒绝 Python 3.10 完整 Hermes v0.19.0 支持 |
| Doctor 3.11/3.12 | exit 0；fake Hermes 0.19.0 与完整已安装环境通过 |
| `/health` | 200，`status=ok` |
| `/ready` | 200，`status=ready` |
| `/version` | 200，`version=3.0.0b1` |
| `POST /memory/tag` | 200；测试内容分类为 `constraint` |
| same-version upgrade | `state=up_to_date`、`changed=false`、同一 Server PID、ready |
| ordinary uninstall | managed adapters/runtime removed；distribution/config/DB preserved |
| pip command contract | 输出精确 uninstall command；产品 CLI 不执行 pip |
| explicit pip uninstall | 仅临时 venv 测试脚本执行；之后 product import 失败 |

上传文本中不存在 fake Secret `fake-qa-art-001-key`。

## 7. 失败与修复记录

### Run #182 / ID `30382147733`

- Python 3.11 的新 wheel+sdist+twine 链路通过；
- Python 3.12 因 no-isolation 当前环境不可导入 `setuptools.build_meta` 失败；
- 修复：显式增加受约束 setuptools 与 wheel dev/build dependencies；
- 未采用：skip、弱化断言、删除 Python 3.12、隐藏失败或绕过 twine。

### Run #183 / ID `30382373294`

三版本完整代码验收全绿，生成 wheel、sdist、twine log、双 inventory、双 SHA256 与 lifecycle JUnit。

### Run #184 / ID `30382668758`

同一最终 PR Head `531aa0e3fd327dc9a096668432ebd1d0b2bff43b` 的 Python 3.10、3.11、3.12 Required jobs 全部成功。

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
| Required Python 3.10/3.11/3.12 final Head CI | PASS |
| artifact/JUnit upload | PASS |
| expected-Head Squash Merge | PASS |
| canonical Issue closure | PASS |

## 9. Reproducibility 与 exclusions

三个 job 的 wheel 与 sdist SHA256 均不同。本 Work ID 证明每个制品可构建、可检查、内容可审计且 wheel lifecycle 通过；不声明 byte-for-byte reproducible build。

后续 canonical owners：

- RC/final reproducibility、SBOM、provenance：`REL-006`；
- 真实 Hermes E2E：`COMPAT-001`；
- Migration：`MIG-001`；
- G1 独立复评：PR #79；
- master、Tag、GitHub Release、PyPI：发布阶段 Work IDs。

**结论：QA-ART-001 与其 G1 remediation 已完整闭环。**
