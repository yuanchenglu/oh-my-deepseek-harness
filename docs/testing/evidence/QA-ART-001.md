# QA-ART-001 Evidence：源码外最终 Wheel 全生命周期

- Work ID：`QA-ART-001`
- Canonical Issue：#25
- Pull Request：#74
- 分支：`test/qa-art-001-external-lifecycle`
- 前置基线：`develop@fc21430b54caac1a8de4cfb1a03940b2b83c25c4`
- 代码验收 Head：`81195f844b681e85ccf2c0a15fc4935b2b396ed6`
- Required CI：Run #161 / ID `30342161995`
- 状态：**ACCEPTED FOR PROTECTED SQUASH MERGE**
- 日期：2026-07-28

> 本证据证明 M1 最终 wheel 可在源码目录外完成 package/artifact lifecycle，不代表 G1 已自动通过，也不代表真实 Hermes E2E、完整 Migration、Public Beta、master、Tag、GitHub Release 或 PyPI publication 已完成。G1 必须在 QA-ART-001 合并和 post-merge 收口后独立判定。

## 1. 唯一 Artifact 验证路径

```text
clean git archive of PR Head
  → build one 3.0.0b1 wheel
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

`scripts/test_artifact.sh` 由 `tests/test_package_artifact.py` 在每个 Required `test (3.10/3.11/3.12)` job 内执行，因此 artifact lifecycle 不能作为非 Required 旁路被跳过。

## 2. Source contamination 防线

每个版本均验证：

- build input 只来自 `git archive HEAD`，不从工作树复制；
- 临时 venv 不使用 editable install；
- `PYTHONPATH` 为空，执行 cwd 位于 repository 和 archived source 之外；
- `deepseek_harness`、`deepseek_context`、`harness_server`、CLI、Doctor、Installer、Lifecycle 的 `__file__` 全部位于临时 venv `site-packages`；
- `sys.path` 不包含 repository 或 archived source；
- wheel 不包含 `plugins/`、`mcp/`、`tests/`；
- ordinary uninstall 后 distribution 仍可 import；只有测试脚本显式执行临时 venv 的 pip uninstall 后 import 才失败。

## 3. Wheel Inventory 与 SHA256

三个 job 各自在其 Python 环境从同一 Git Head 构建纯 Python wheel：

| Python | Wheel | Files | SHA256 |
|---|---|---:|---|
| 3.10 | `oh_my_deepseek_harness-3.0.0b1-py3-none-any.whl` | 39 | `d0e3400535971dc63bfc04427aee7a1cff9ef772e4e4acd5c5d6735ac7daec6f` |
| 3.11 | `oh_my_deepseek_harness-3.0.0b1-py3-none-any.whl` | 39 | `36ad9c41be70d8e946ec2026f2fd6c8b57c1b5314b5765966a728dc92a277985` |
| 3.12 | `oh_my_deepseek_harness-3.0.0b1-py3-none-any.whl` | 39 | `536961ebcb87e1646158901953de5592b17517d1d54bc36c790525759c116c36` |

Hash 不同表示普通 wheel build 尚未声明跨 job byte-for-byte reproducible；该结论不阻塞 QA-ART-001，因为本 Work ID 固定并验证每个实际制品，最终 RC reproducibility 仍由 `REL-006` 验证。不得把本证据描述为 reproducible-build PASS。

## 4. Lifecycle 证据

每个 Python job 均完成：

| 阶段 | 固定结果 |
|---|---|
| install dry-run | exit 0；data root 不存在；零持久写入 |
| clean install | packaged adapters/config/DB/runtime；一个 ready Server |
| Doctor 3.10 | exit 5；明确拒绝 Python 3.10 作为完整 Hermes v0.19.0 支持 |
| Doctor 3.11/3.12 | exit 0；fake Hermes 0.19.0 与完整已安装环境通过 |
| `/health` | 200，`status=ok` |
| `/ready` | 200，`status=ready` |
| `/version` | 200，`version=3.0.0b1` |
| `POST /memory/tag` | 200；`must not expose secrets` 分类为 `constraint` |
| upgrade dry-run | exit 0；报告 same-version lifecycle |
| same-version upgrade | `state=up_to_date`、`changed=false`、同一个 Server PID、ready |
| ordinary uninstall | managed adapters/runtime removed；distribution/config/DB preserved |
| pip command contract | 输出 `python -m pip uninstall oh-my-deepseek-harness`；产品 CLI 不执行 pip |
| explicit pip uninstall | 仅测试脚本在临时 venv 执行；之后 product import 失败 |

上传文本中不存在 fake Secret `fake-qa-art-001-key`。

## 5. CI 与 Artifacts

### 5.1 首轮

Run #160 / ID `30341906435`，Head `41d7052b2a12817199700d22f61dc9f2f0b5c0eb`：

- 三版本的外部 artifact lifecycle 已完整执行并生成成功 artifact JUnit；
- pytest 仅因静态契约测试未包含 shell 变量的双引号而失败；
- 未修改或弱化 artifact lifecycle，修正测试字符串后重跑完整矩阵。

### 5.2 代码验收

Run #161 / ID `30342161995`，Head `81195f844b681e85ccf2c0a15fc4935b2b396ed6`：

```text
Python 3.10: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.11: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.12: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
```

每个 job 另包含 artifact JUnit：1 test / 0 failures / 0 errors / 0 skipped。

GitHub Actions artifacts：

- Python 3.10：artifact `8681477786`，archive digest `sha256:05d1a3f2299fdf5cd398702ddd27dadadea52c47c2802a0a81fc758943b09959`；
- Python 3.11：artifact `8681477180`，archive digest `sha256:c886340d8e3711236e9f5a426c43a09692ae4785eb64e8182c7a55085980c60d`；
- Python 3.12：artifact `8681471488`，archive digest `sha256:9eb8a1c6175d1e28dbd38833279b477913be1cdf01d5ba05243d70cde940bb29`。

每个 artifact 包含：pytest JUnit、artifact JUnit、wheel、SHA256、完整 inventory、build/install logs、import probe、install/Doctor/Server/upgrade/uninstall JSON 与 explicit pip-uninstall log。

## 6. DoD 判定

| 验收项 | 结果 |
|---|---|
| clean source snapshot build | PASS |
| wheel filename/version/39-file inventory/SHA256 | PASS |
| fresh non-editable venv only installs final wheel distribution | PASS |
| no repository/archived-source product imports | PASS |
| temporary HOME/data/DB/dynamic port/fake secret | PASS |
| install dry-run + clean install | PASS |
| Doctor support/rejection matrix | PASS |
| health/ready/version | PASS |
| minimal Tool/API smoke | PASS |
| same-version upgrade dry-run + idempotent upgrade | PASS |
| ordinary uninstall preserves distribution and data | PASS |
| product CLI never invokes pip | PASS |
| explicit pip uninstall limited to temporary venv | PASS |
| Required Python 3.10/3.11/3.12 CI | PASS |
| artifact/JUnit upload | PASS |
| real user HOME/source PYTHONPATH/editable install | NOT USED |

**结论：QA-ART-001 已达到 Ready-for-Review 与 protected Squash Merge 条件；只有 PR #74 实际合入 develop 且 Issue #25 关闭后，Work ID 才正式 Complete。G1 必须随后独立评估。**

## 7. 明确不在本 Work ID 内

- wheel byte-for-byte reproducibility 判定；
- sdist/final RC provenance 或 SBOM；
- 真实 Hermes discovery/enable/Hook/Context/Tool E2E；
- package/runtime/lifecycle 实现变更；
-完整 Migration；
- G1 自动 PASS；
- master、Tag、GitHub Release 或 PyPI publication。
