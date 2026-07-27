# 开源发布执行计划（Open-source Release Execution Plan）

> 文档版本：2.2
>
> 审查基线：`develop@37e4016`
>
> 计划状态：`READY_FOR_IMPLEMENTATION`
>
> 适用分支：`develop`
>
> 发布目标：`v3.0.0-beta.1` → 按需增加 Beta → `v3.0.0`
>
> 关联文档：[`PRD`](../product/PRD.md) · [`技术架构`](../architecture/TECHNICAL_ARCHITECTURE.md) · [`Code Review`](../reviews/CODE_REVIEW_2026-07-27.md) · [`测试计划`](../testing/TEST_PLAN.md) · [`测试报告`](../testing/TEST_REPORT_2026-07-27.md)

## 更新记录（Update Log）

| 日期 | 版本 | 更新内容 | 来源 |
|---|---|---|---|
| 2026-07-27 | 1.0 | 建立开源发布 Roadmap 初稿 | 产品、架构、Code Review 和测试基线 |
| 2026-07-27 | 2.0 | 修正版本回退、M0 状态、制品缺口、缺陷遗漏、Tool 数量、分支冲突、不可测指标和无依据工期；增加 Gate、追踪矩阵、风险与回滚 | 严格计划审查 + 干净 Git 制品验证 |
| 2026-07-27 | 2.1 | 区分“计划已就绪”和“G0 尚未执行”；补充代理执行协议、逐任务文件边界、完整需求覆盖、命令、交付证据和停止条件 | 用户要求交付给能力较弱的实施 AI |
| 2026-07-27 | 2.2 | 固定 48 个 Work ID/Issue 关系和 12 个 XFAIL node；将 Beta Migration 前移至 G3；补齐 M5/M6 依赖、GitHub Ruleset、provenance 与安全验收 | 最终可执行性与三层闭环校验 |

## 1. 当前结论

### 1.1 发布判断

当前代码只能作为 **Experimental Preview**，不满足 Public Beta Gate，更不满足 Stable Gate。

已确认基线：

- Python 3.10、3.11、3.12 CI 中每个版本均为 144 Passed、12 strict XFAIL；
- 12 个 XFAIL 对应已知 P0/P1 缺陷，不得把绿色 CI 解释为产品可发布；
- 当前安装脚本没有安装 Harness Server 和完整 Runtime；
- 当前从干净 Git 快照构建的 wheel 不含 `mcp/harness_server`、插件 YAML/策略配置或 Console Script，在源码目录外无法导入目标插件包；
- G0 的仓库治理、Issue 和外部兼容性验证尚未执行；这是实施阶段的第一批任务，不再是计划文档缺口。

### 1.2 Plan Ready Gate

本计划已经达到 **可进入实施阶段** 的标准。`G0` 是第一个实施 Gate，不是“继续写计划”的 Gate；实施代理必须从 `REL-000` 开始，不得跳到 M1。

- [x] 当前行为和 Release Blocker 有源码、测试或审查证据；
- [x] 版本、制品、CLI、Tool 数、支持范围和分支策略已固定；
- [x] 48 个 Work ID 均有依赖、文件边界、测试入口、完成证据和退出 Gate；现有 83 个 Test ID 与新增预留的 17 个 Test ID 均有主责；
- [x] 88 个 `FR-*` 已按需求域映射到 Work ID 和测试范围；
- [x] 所有 5 个 P0、7 个 P1、5 个 P2 均进入追踪基线；
- [x] 未决外部事实已隔离为显式验证任务，不要求实施 AI 猜测；
- [x] 定义了实施顺序、停止条件、验证命令和交付格式；
- [x] G0–G5 均使用可复现证据判定。

计划完成度结论：文件层、任务依赖层、交付管线层均闭合。允许开始 M0；在 G0 通过前仍禁止开始 M1。

### 1.3 第一性目标

所有近期工作只服务于以下五个问题：

1. 用户能否从最终发布制品安装、启动、诊断、升级和卸载？
2. Context、Session、Memory、Plan 和 Checkpoint 是否保持数据不变量？
3. 外部数据发送是否透明、可关闭、可审计且完成脱敏？
4. 外部贡献者能否在不理解全部代码的情况下验证修改？
5. Release Gate 能否由可复现证据自动判定，而不是由主观判断放行？

不直接提高上述五项的工作不进入本发布周期。

## 2. 已固定的发布决策

### 2.1 版本策略

同一发行身份不得从现有 `2.x` 回退到 `0.x`。本周期采用：

- Git Tag / GitHub Release：`v3.0.0-beta.1`；
- Python Distribution：`3.0.0b1`；
- Plugin Manifest：`3.0.0-beta.1`；
- 如 Beta 需要修订，递增 `beta.2`、`beta.3`；
- Stable 仅在全部 Stable Gate 通过后发布 `v3.0.0`。

选择 `3.0.0` 是因为标准 package、安装路径、生命周期和迁移机制会发生破坏性变化。只有创建新的 distribution 身份时，才允许重新从 `0.x` 起步。[→附录 Q#1]

### 2.2 发布制品

Public Beta 的最小发布集合为：

1. Python wheel；
2. Source distribution；
3. `SHA256SUMS`；
4. 依赖 SBOM；
5. Release Notes 与 Known Limitations；
6. 由 GitHub Release Workflow 生成的 Artifact Attestation；
7. 对应不可变 Git Tag。

GitHub Release 是 Beta 必须提供的制品渠道。PyPI 发布必须在 M0 验证名称所有权和维护者权限后才能启用；PyPI 不是绕过制品验证的替代方案。[→附录 Q#2]

### 2.3 目标安装与 CLI 契约

最终安装流程必须等价于：

```bash
python -m pip install "oh-my-deepseek-harness[all]==3.0.0b1"
deepseek-harness install
deepseek-harness doctor
```

从审查基线迁移到首个 Beta 的顺序固定为：

```bash
python -m pip install --upgrade "oh-my-deepseek-harness[all]==3.0.0b1"
deepseek-harness upgrade --dry-run
deepseek-harness upgrade
deepseek-harness doctor
```

Python distribution 只由 pip 管理；`deepseek-harness` CLI 不得调用 pip 安装、升级或卸载自己。Beta 的公开 CLI 固定为：

```bash
deepseek-harness install
deepseek-harness install --dry-run
deepseek-harness doctor
deepseek-harness doctor --json
deepseek-harness upgrade
deepseek-harness upgrade --dry-run
deepseek-harness server start
deepseek-harness server status
deepseek-harness server stop
deepseek-harness server restart
deepseek-harness audit
deepseek-harness audit --json
deepseek-harness memory import PATH
deepseek-harness memory import PATH --dry-run
deepseek-harness memory delete --id MEMORY_ID --confirm
deepseek-harness memory delete --source SOURCE --confirm
deepseek-harness plan show PLAN_ID
deepseek-harness plan show PLAN_ID --include-archived
deepseek-harness plan archive PLAN_ID
deepseek-harness plan delete PLAN_ID --confirm
deepseek-harness uninstall
deepseek-harness uninstall --dry-run
deepseek-harness uninstall --purge-data --confirm
```

`install` 把已安装 distribution 中的薄适配入口和 manifest 注册到 Hermes；`upgrade` 只迁移部署、配置和数据。普通 `uninstall` 停止 Server 并移除 Hermes 注册、薄适配文件和 runtime state，保留 Python distribution 与用户数据，最后打印精确的 `python -m pip uninstall oh-my-deepseek-harness` 命令。`--purge-data` 额外删除 §2.8 的产品数据根，必须同时提供 `--confirm`；所有 delete 命令缺少 `--confirm` 时只显示影响范围并以退出码 2 拒绝执行。

CLI 退出码固定为：

| 退出码 | 含义 |
|---:|---|
| 0 | 命令完成，所有承诺的后置条件成立 |
| 2 | 参数/输入校验失败，或破坏性命令缺少 `--confirm`；无持久化变化 |
| 3 | Python/Hermes/依赖/配置等环境前置条件不满足；无迁移写入 |
| 4 | Server、端口、DB 或外部 Provider 运行失败；不得留下新增半状态 |
| 5 | install/upgrade 失败但 rollback 已完整恢复，可继续使用旧版本 |
| 6 | rollback 未完整恢复；按 P0 处理并输出人工恢复步骤 |

`doctor --json` 和 `audit --json` 的 stdout 只能输出一个 JSON object，固定顶层字段为 `status`、`command`、`version`、`checks`、`errors`、`next_actions`。`status` 只能是 `ok`、`degraded`、`error`；每个 check 固定包含 `name/status/message`，每个 error 固定包含 `code/message/recovery`，`next_actions` 是字符串数组。诊断文本写 stderr，任何输出均不得包含 Secret 或未经脱敏的用户内容。

上述命令、参数和退出语义是本周期固定外部契约；Memory/Plan CLI 不增加公共 Hermes Tool 数。除非证明确认的 Hermes 正式版本无法承载该契约，否则不得修改；如必须修改，先提交 ADR 并同步本计划、PRD、测试和 README。

### 2.4 Tool 清单

Beta 目标为 **10 个公共 Tool**：[→附录 Q#3]

| 领域 | Tool |
|---|---|
| Plan | `plan_create`、`plan_update_step`、`plan_cascade`、`plan_status` |
| Memory | `memory_tag`、`memory_store`、`memory_query`、`memory_filter` |
| Checkpoint | `checkpoint_create`、`checkpoint_review` |

`checkpoint_chain` 保持内部 API，不计入公共 Tool Contract。任何 Tool 增删必须同时更新 Pydantic Model、生成 Schema、Contract Test、README 和本表。

API 与 Tool 共用以下响应 envelope；字段不得按端点增删：

```json
{
  "ok": true,
  "data": {},
  "error": null,
  "meta": {"request_id": "...", "server_version": "..."}
}
```

```json
{
  "ok": false,
  "data": null,
  "error": {"code": "not_found", "message": "...", "recovery": "..."},
  "meta": {"request_id": "...", "server_version": "..."}
}
```

错误码与 HTTP 状态固定映射为：`validation_error` → 422、`not_found` → 404、`conflict` → 409、`server_unavailable` → 503、`timeout` → 504、`internal_error` → 500。Tool Handler 返回上述 JSON object 的序列化字符串，即使 Server 不可达也不得退回 `{"error": "..."}`；`message` 不含原始异常、绝对路径或 Secret，`recovery` 给出用户可执行的下一步。

Runtime 探针契约固定为：

| Endpoint | 成功 | 失败/约束 |
|---|---|---|
| `GET /health` | 只验证进程/Event Loop，200，`data.status=alive` | 不访问 DB、Provider 或用户文件 |
| `GET /ready` | DB 可连接、migration 完成且必需 Service 已装配时 200，`data.status=ready` | 未就绪返回 503 + `server_unavailable` envelope |
| `GET /version` | 200；`data` 固定含 `distribution_version`、`server_version`、`config_schema_version`、`db_schema_version`、`hermes_target` | 不返回绝对路径、环境变量或 Secret |

### 2.5 支持范围

- 操作系统：Linux、macOS；
- Python：3.10、3.11、3.12；
- Python 元数据在扩展 CI 前必须声明 `<3.13`；
- Hermes：Beta 只支持一个经过真实 E2E 的正式版本，具体版本由 `COMPAT-000` 决定；
- Summary Provider：Beta 只承诺 DeepSeek OpenAI-compatible API 和测试 Fake；
- Server：仅监听 loopback，单机单进程。

### 2.6 分支策略

- `master`：只保存通过 Release Gate 的可发布基线；
- `develop`：本周期唯一集成分支，并设为 GitHub 默认分支；
- `fix/<scope>`、`test/<scope>`、`docs/<scope>`、`chore/<scope>`：从 `develop` 创建并通过 PR 合回 `develop`；
- Release Candidate 通过 G3 后，由 `develop` 发起 PR 合入 `master`；
- 禁止直接向 `master` 或 `develop` 推送业务变更。

M0 必须同步修改 CONTRIBUTING 和 PR 模板；经用户明确授权后，把 GitHub 默认分支设为 `develop`，并为 `master`、`develop` 启用禁止强推/删除且必须经 PR 合入的 Ruleset。G0 先要求当前 CI 为 Required Check，M4 再把新增质量检查加入 Required Checks。未获仓库管理权限时不得声称 G0 通过。[→附录 Q#4]

### 2.7 Cron 决策

Beta **不自动修改** 用户的 crontab、systemd 或 launchd。`crons/immune-audit.cron` 降级为示例配置；正式支持的入口是手工命令：

```bash
deepseek-harness audit
```

README 必须把自动定时审计标记为 Experimental，并分别提供 Linux/macOS 示例。安装、升级和卸载不得创建或删除用户定时任务。[→附录 Q#7]

### 2.8 安全默认值与运行目录

非交互安装使用以下安全默认值：

```yaml
server:
  host: 127.0.0.1
  port: 8200
summary:
  enabled: false
  outbound_policy: redact
  allow_tool_arguments: false
memory:
  import_on_startup: false
logging:
  include_content: false
```

交互安装只有在展示外发说明并获得用户明确选择后才能启用 Summary。环境变量只允许以下稳定名称；Plugin、CLI 和 Server 必须共用，不得保留 `HARNESS_SERVER_PORT` 或另设同义变量：

| 配置 | 环境变量 | 说明 |
|---|---|---|
| 配置文件 | `HARNESS_CONFIG_PATH` | 未设置时使用下方默认路径 |
| 数据根 | `HARNESS_DATA_ROOT` | 未设置时为 `~/.hermes/oh-my-deepseek-harness` |
| SQLite | `HARNESS_DB_PATH` | 测试/高级覆盖；不自动扩大 purge 范围 |
| Server Host | `HARNESS_HOST` | Plugin 与 Server 共用，默认 `127.0.0.1` |
| Server Port | `HARNESS_PORT` | Plugin 与 Server 共用，默认 `8200` |
| Summary 开关 | `HARNESS_SUMMARY_ENABLED` | 只接受 `true/false/1/0`，非法值按退出码 3 拒绝 |
| Summary 外发策略 | `HARNESS_SUMMARY_OUTBOUND_POLICY` | Beta 只接受 `redact` |
| Tool 参数外发 | `HARNESS_SUMMARY_ALLOW_TOOL_ARGUMENTS` | 默认 false；Beta 不允许改为 true |
| Memory 启动导入 | `HARNESS_MEMORY_IMPORT_ON_STARTUP` | 默认 false |
| 日志内容 | `HARNESS_LOG_INCLUDE_CONTENT` | 默认 false；Beta 不允许改为 true |
| Provider 凭证 | `DEEPSEEK_API_KEY` | 只从环境读取，不写配置/日志 |
| Provider 地址 | `DEEPSEEK_BASE_URL` | 默认 `https://api.deepseek.com`；自定义地址仍受外发提示与脱敏规则约束 |

`HARNESS_DB_PATH` 若位于规范化 `HARNESS_DATA_ROOT` 之外，普通 uninstall 和 `--purge-data` 都必须保留该文件并报告人工处理路径；symlink 解析后越出数据根也按外部路径处理。配置优先级固定为：CLI > Environment > User Config > Package Defaults。

```text
~/.hermes/oh-my-deepseek-harness/
├── config/config.yaml
├── data/harness.db
├── logs/harness-server.log
├── events/constraint-events.jsonl
├── runtime/server.json
└── backups/
```

目录默认权限 `0700`，配置、数据、事件、日志和 runtime 文件默认权限 `0600`。运行数据不得写回 Git 仓库；普通卸载保留 `config/`、`data/`、`events/` 和 `backups/`。

## 3. 实施代理执行协议

本节对所有 Work ID 强制生效。任何实施 AI 均按以下顺序工作，不得把“文件存在”或“测试收集成功”当成交付完成。

### 3.1 单任务边界

1. 一次只领取一个 Work ID；
2. 只修改附录 A 允许的文件；发现必须跨界时先停止并说明原因；
3. 修改前声明一个可证伪假设，并引用源码、测试或文档依据；
4. 先运行基线测试，再最小实现，再运行目标测试和回归测试；
5. strict XFAIL 修复后必须删除标记，禁止改成 skip、放宽断言或新增重试；
6. 不得顺手重构、重命名无关符号或批量格式化无关文件；
7. 一个 Work ID 对应一个执行 Issue，一个 Commit 只对应一个 Work ID，并遵守仓库双语 Commit 规范；
8. §7 中每个 P0/P1 的首个 Work ID 是该缺陷的主责 Issue；其余 Work ID 是关联 Issue，必须反向链接主责 Issue；
9. 开始前检查所有进行中 Issue 的“允许修改”路径；存在交集时不得并行，后启动者等待前一任务合入并 rebase 后再跑基线。

### 3.2 三层验证

每个任务必须同时给出三层证据：

| 层级 | 必须证明 | 不接受 |
|---|---|---|
| 文件层 | 目标代码、配置、数据文件存在且可解析/构建 | 仅列文件名 |
| 集成层 | 调用方真实 import 并调用新实现，依赖不是 `None`、Mock 或源码 symlink | 只测孤立函数 |
| 管线层 | 用户入口 → Plugin/CLI → Server/Context/Storage → 可观察结果完整通过 | 只说 CI 绿色 |

### 3.3 通用前置检查

```bash
git status --short
git branch --show-current
python --version
test_home=$(mktemp -d)
mkdir -p "$test_home/home" "$test_home/data"
test_port=$(python -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')
env \
  HOME="$test_home/home" \
  HARNESS_CONFIG_PATH="$test_home/data/config/config.yaml" \
  HARNESS_DATA_ROOT="$test_home/data" \
  HARNESS_DB_PATH="$test_home/data/harness.db" \
  HARNESS_PORT="$test_port" \
  DEEPSEEK_API_KEY=fake \
  python -m pytest --collect-only -q
```

要求：

- 当前分支必须从 `develop` 创建；
- 工作区已有改动视为用户资产，不得覆盖；
- 测试必须使用临时 HOME、DB 和动态端口；
- 缺依赖时允许创建项目内 `.venv`，但不得把环境文件提交；
- 依赖安装因网络或权限失败时，报告阻断，不得声称测试通过。

### 3.4 通用完成命令

在 `make test-fast` 尚未由 `QA-001` 建立前，至少运行目标测试文件和当前完整 pytest；建立后统一使用：

```bash
make test-fast
make test-integration
git diff --check
git status --short
```

Release 类 Work ID 还必须运行 `make test-release`。命令失败即任务未完成。

### 3.5 强制停止条件

遇到以下任一情况，实施代理必须停止并请求决策：

- 需要修改附录 A 未授权的业务域；
- 需要删除或迁移用户数据，但没有可恢复备份和 rollback 测试；
- 需要真实 Token、PyPI/GitHub 发布权限或用户账号；
- Hermes 实际接口与 `COMPAT-000` 记录不一致；
- 目标测试无法稳定复现缺陷；
- 新依赖会改变许可证、安全或支持平台；
- 发现新的 P0，或现有通过测试发生非预期回归；
- 需求、Schema 和现有数据无法同时兼容。

### 3.6 标准交付格式

每个 Work ID 的交付说明必须按以下顺序：

1. Work ID 与结论；
2. 修改前假设、证据和最终判断；
3. 修改文件清单；
4. 三层验证证据；
5. 测试命令及 Passed/Failed/XFAIL 数量；
6. Gate 清单中被关闭的条目；
7. 未解决风险、Waiver 或后续依赖；
8. Commit SHA（如任务要求提交）。

Release Blocker 的证据摘要写入 `docs/testing/evidence/<WORK-ID>.md`；原始 JUnit、wheel 清单和扫描结果作为 CI Artifact 保存，文档只保存 Run URL、SHA256、环境和结论。

Commit 必须使用：

```text
<type>(<scope>): English title | 简体中文标题

English:
<what changed, why, and verification>

简体中文:
<改了什么、为什么、如何验证>
```

### 3.7 目标源码布局

M1 完成后必须收敛为以下单一源码结构：

```text
src/
├── deepseek_harness/       # Hook、Session、Tool Adapter、CLI、Installer
│   └── resources/          # plugin.yaml、strategies.yaml、Hermes 薄适配入口
├── deepseek_context/       # Context Engine、Compressor、Redaction
│   └── resources/          # plugin.yaml、config.yaml、Hermes 薄适配入口
└── harness_server/         # App Factory、Models、Storage、Runtime Supervisor
```

迁移规则：

- `plugins/deepseek-harness/*.py` 移入 `src/deepseek_harness/`；
- `plugins/deepseek-context/*.py` 移入 `src/deepseek_context/`；
- `mcp/harness_server/*.py` 移入 `src/harness_server/`；
- 旧目录不得保留第二份业务实现；如 Hermes 要求连字符目录，只允许安装器部署 manifest 和转发到已安装 package 的薄适配代码；
- `scripts/install.sh` 在过渡期只能调用 `deepseek-harness install`，不得继续维护第二套安装逻辑；
- `tests/conftest.py` 必须删除创建下划线 symlink 的逻辑；测试只 import 已安装 package；
- package data 使用构建配置显式声明，并由 wheel 内容测试锁定。

在 `COMPAT-000` 完成前不得猜测 Hermes 的插件发现协议；如果目标 Hermes 不支持薄适配入口，停止 PKG-001 并提交证据，不得复制业务源码规避问题。

## 4. 严重度与发布政策

| 级别 | 定义 | Beta | Stable |
|---|---|---|---|
| P0 / Blocker | 无法安装、核心链路不可用、数据损坏、跨 Session 污染、未披露敏感数据外发 | 必须为 0 | 必须为 0 |
| P1 / Critical | 关键能力不可靠、跨模块契约错误、长期运行产生严重数据问题 | 仅允许书面 Waiver | 必须为 0 |
| P2 / Major | 工程质量、可维护性、可观测性或产品表述问题 | 可排期，但不得导致误导性文案 | 应有明确版本计划 |

Beta P1 Waiver 必须包含：缺陷 ID、影响范围、复现证据、临时缓解、Owner、失效日期和关闭版本。缺任一字段不得放行。

## 5. Release Gates

Plan Ready Gate 已通过，可以开始 M0。前一执行 Gate 未通过时，不得开始下一 Milestone，也不得启动依赖其产物的公开发布活动。

G0–G5 不是实现 Work ID。Gate 协调者在目标 Commit 上逐项复核，并写入 `docs/testing/evidence/GATE-G<N>.md`：Commit SHA、每个复选项的证据链接/命令/计数、P0/P1 查询、Waiver、结论和复核人。缺证据的复选项保持未勾选；只有报告结论为 `PASS` 才能更新本计划状态和开始下一阶段。实施该功能的 AI 不得仅凭自己的交付说明自判 Gate 通过。

### G0：规格与治理就绪

- [ ] 版本、发行渠道、CLI、10 个 Tool 和支持范围全部形成决策记录；
- [ ] README、CONTRIBUTING、PRD、测试计划中的版本与分支口径一致；
- [ ] GitHub 默认分支为 `develop`；`master`、`develop` 禁止强推/删除并要求 PR，当前 CI 是 Required Check；
- [ ] 48 个 Work ID 各有一个执行 Issue；5 个 P0、7 个 P1 各有唯一主责 Issue，并链接所有关联 Issue；
- [ ] 每个 Release Blocker 均能追踪到 Requirement、CR/XF、TC、Issue、PR；
- [ ] 每个 Issue 有 Owner、估算、依赖、验收测试和回滚说明；
- [x] 首次 Python 3.10–3.12 CI 完整测试报告存在；
- [ ] 建立 `SECURITY.md`、Issue/PR 模板和 Release Checklist；
- [ ] 完成 PyPI 名称与权限验证；若不可用，明确记录 GitHub-only Beta 决策；
- [ ] 确认一个待验证的 Hermes 正式版本。

### G1：制品与 Runtime 就绪

- [ ] 从干净 Git Tag 构建 wheel 和 sdist；
- [ ] `python -m twine check dist/*` 通过；
- [ ] wheel 包含 Server、Plugin、Context、YAML/策略和必要 package data；
- [ ] 在源码目录外可导入所有公共 package；
- [ ] wheel 安装后不依赖源码 symlink 或仓库相对路径；
- [ ] Console Script 可启动、检查、停止 Server；
- [ ] `/health`、`/ready`、`/version` 行为满足契约；
- [ ] 空 HOME 下完成 pip install → install → doctor → smoke → 普通 uninstall → pip uninstall；
- [ ] 重复安装、端口占用、安装中断和卸载保留数据测试通过；
- [ ] 安装和测试不读取或修改真实 `~/.hermes`。

### G2：核心完整性就绪

- [ ] Context 三个 strict XFAIL 转为普通 Pass；
- [ ] Summary 失败完整 rollback，输入对象不被原地修改；
- [ ] 受保护消息逐字保留，消息不重复，Tool Pair 顺序合法；
- [ ] 输出 Token 不下降时 rollback；
- [ ] Session 状态按 `session_id` 隔离并在结束时清理；
- [ ] 并发 Session 测试通过；
- [ ] Secret Redaction 覆盖外发请求与日志；
- [ ] 外部 Summary 可关闭，并记录不含原 Prompt 的诊断事件；
- [ ] 所有 P0 为 0。

### G3：Beta Release Candidate 就绪

- [ ] 全量 Release Test 中 Failed = 0、XPASS = 0、XFAIL = 0；
- [ ] P0 = 0；P1 已关闭或具备第 4 节定义的有效 Beta Waiver；
- [ ] 10 个 Tool Contract 100% 通过；
- [ ] Memory Store/Query/Delete/Dry-run/Import 契约通过，重启导入重复率为 0；
- [ ] Plan DAG、状态机、事务、Query/Archive/Delete 不变量测试通过；
- [ ] Checkpoint 归属、编号和幂等测试通过；
- [ ] Audit 事件格式一致，手工 `audit` 命令可用，Cron 示例标为 Experimental；
- [ ] Intent 低置信回退与否定语义数据集测试通过；
- [ ] `TC-MIG-001–006` 覆盖从审查基线版本升级、迁移失败回滚和旧程序拒绝新 Schema，并全部通过；
- [ ] Linux/macOS 与 Python 3.10–3.12 支持矩阵通过；
- [ ] 真实 Hermes 版本 E2E 通过；
- [ ] Local API、文件权限、输入限制、Prompt Injection 和破坏性操作安全边界测试通过；
- [ ] Ruff、类型检查、ShellCheck、依赖漏洞和 Secret 扫描通过；
- [ ] 依赖无未豁免 High/Critical 漏洞；
- [ ] README 能力分级、隐私说明、安装、升级、Doctor、卸载、Troubleshooting 和 Known Limitations 完成；
- [ ] Release 制品、SHA256、SBOM、provenance 和 Release Notes 生成成功。

### G4：Public Beta 验证通过

- [ ] 满足第 9 节的样本量与指标定义；
- [ ] Beta 期间没有确认的数据损坏或跨 Session 污染；
- [ ] 所有失败均有诊断记录和根因分类；
- [ ] P0 为 0；P1 均已关闭或具备有效 Beta Waiver；
- [ ] 发布后回滚和撤回演练通过。

### G5：Stable 就绪

- [ ] G0–G4 全部通过；
- [ ] P0 = 0，P1 = 0；
- [ ] Clean install、Upgrade、Downgrade 拒绝、Uninstall 和失败回滚通过；
- [ ] Config/DB Schema version 与 Migration 测试通过；
- [ ] Context Property Tests 和 Session 并发隔离持续通过；
- [ ] 至少 14 个连续日历日、满足规定暴露量且无数据完整性 P0；
- [ ] 安全审查、第三方许可证核查和依赖审计完成；
- [ ] README、Changelog、待发布 Tag 名、package metadata 与实际能力一致。

## 6. 工作分解与依赖顺序

估算使用净工程人日，不包含等待外部用户反馈的日历时间。默认 Owner 为核心维护者；创建 Issue 时必须替换为具体人员。

### 6.1 强制执行顺序

```text
M0:
REL-000 → REL-001 → REL-002 → REL-004 → GOV-001 → REL-003
REL-000 → REL-005
REL-000 → COMPAT-000
REL-003 + REL-005 + COMPAT-000 → G0

M1:
COMPAT-000 → PKG-001 → PKG-002 → RUN-001 → RUN-002 → INS-001 → INS-002 → INS-003 → QA-ART-001 → G1

M2:
CTX-001 → CTX-002 → CTX-003 → CTX-004
PKG-001 → SES-001
CTX-003 + SES-001 → PRIV-001
CTX-004 + PRIV-001 → G2

M3:
PKG-001 → CON-001
CON-001 → MEM-001 → MEM-002 → PLAN-001 → PLAN-002 → PLAN-003 → CP-001
SES-001 → AUD-001 → OPS-001
INTENT-001 可在 CON-001 后独立执行
全部完成 → M4

M4:
DOC-001 → DOC-002
QA-001 → QA-002
COMPAT-000 + QA-002 → COMPAT-001
COMPAT-001 + PRIV-001 → SEC-001
INS-003 + MEM-002 + AUD-001 → MIG-001
SEC-001 + MIG-001 → SEC-002
以上全部完成 → REL-006 → G3

M5:
G3 → BETA-001
BETA-001 → BETA-002
BETA-001 → REL-007
BETA-002 + BETA-003 + REL-007 → G4

M6:
G4 → STABLE-001
STABLE-001 → SOAK-001
SOAK-001 → G5 → REL-008
```

同一箭头左侧是右侧硬依赖。没有列出的并行关系也不得跨 Gate 提前实施。

### 6.2 M0：规格、治理与发布契约

状态：未开始；这是 Plan Ready 后的第一个实施 Milestone。

估算：3–5 人日。退出：G0。

| Work ID | 工作 | 依赖 | 验收 |
|---|---|---|---|
| REL-000 | 将本计划 §2 的固定契约和 §7.2.2 预留测试同步到 PRD、架构和测试计划 | 无 | 版本、Tool、默认值、路径、CLI、支持范围、测试 ID 无冲突 |
| REL-001 | 统一逻辑版本、Python 版本、Plugin 版本和 Tag 规则 | REL-000 | 版本 ADR、迁移规则、Changelog 规则一致 |
| REL-002 | 统一 `develop`/`master` 工作流和 GitHub 分支设置 | REL-001 | Roadmap、CONTRIBUTING、PR 模板、默认分支、Ruleset 和当前 Required Check 一致 |
| REL-004 | 固定 10 个公共 Tool 清单 | REL-002 | Schema、测试计划和文档分母一致 |
| REL-005 | 验证 PyPI 名称与发布权限 | REL-000 | 留存权限验证结果，不记录 Token 或其他 Secret |
| COMPAT-000 | 选择待验证的 Hermes 正式版本 | REL-000 | 记录版本、来源和完整 E2E 方案 |
| GOV-001 | 增加安全、Issue/PR 和 Release 治理文件 | REL-004 | 模板可直接创建合格 Issue/PR |
| REL-003 | 创建执行 Issue 并建立完整追踪矩阵 | GOV-001 | 48 个 Work ID 各有 Issue；所有 Release Blocker 可追踪到测试和主责/关联 Issue |

### 6.3 M1：可复现制品与 Runtime

状态：未开始。

估算：8–12 人日。依赖：M0。退出：G1。

| Work ID | 工作 | 关键验收 |
|---|---|---|
| PKG-001 | 使用标准 package layout，纳入 Plugin、Context、Server 和 package data | 干净快照 wheel 在源码外可导入 |
| PKG-002 | 定义 `context`、`server`、`all`、`dev` extras | 实际 import 与依赖声明一致 |
| RUN-001 | App Factory、§2.8 唯一环境变量、loopback 和 `/health` `/ready` `/version` | Process Integration 全通过；旧 `HARNESS_SERVER_PORT`/`HARNESS_SERVER_URL` 引用为 0 |
| RUN-002 | Process Supervisor、PID/runtime state、日志、start/status/stop/restart | 重复启动不产生双进程，失败可诊断 |
| INS-001 | Dry-run、Clean install 和幂等重复安装 | TC-INSTALL-001–003 通过 |
| INS-002 | Doctor、依赖/版本检查和端口诊断 | `TC-INSTALL-004`、`TC-INSTALL-005`、`TC-INSTALL-009` 通过 |
| INS-003 | Upgrade、普通卸载、`--purge-data --confirm` 防护和中断恢复 | `TC-INSTALL-006–008`、`TC-INSTALL-010` + Upgrade 夹具通过；CLI 不调用 pip |
| QA-ART-001 | 最终制品 E2E 和制品内容断言 | CI 只安装 wheel，不从源码 import |

### 6.4 M2：Context、Session 与隐私完整性

状态：未开始。

估算：6–10 人日。依赖：M1 的 App Factory 和测试隔离。退出：G2。

| Work ID | 工作 | 关键验收 |
|---|---|---|
| CTX-001 | 删除 Merge 分支重复装配 | `TC-CTX-003` Pass |
| CTX-002 | Summary 失败返回完整原消息 | `TC-CTX-004`、`TC-CTX-005`、`TC-CTX-006` Pass |
| CTX-003 | Stable Message ID、Protected Message、Tool Pair Validator | `TC-CTX-007`、`TC-CTX-008`、`TC-CTX-009`、`TC-CTX-014` Pass |
| CTX-004 | 压缩阈值/正常路径、Token 不降 rollback、输入不可变和跨 Session Summary 隔离 | `TC-CTX-001`、`TC-CTX-002`、`TC-CTX-011–013` Pass |
| SES-001 | `SessionPolicyStore`、Session End Cleanup、移除模块级共享状态 | `TC-POLICY-001–005` Pass |
| PRIV-001 | 外发/日志 Secret Redaction、关闭开关、数据发送提示和审计 | `TC-CTX-010`、`TC-SEC-001` Pass |

### 6.5 M3：Contract 与 Data Integrity

状态：未开始。

估算：8–13 人日。依赖：M1；涉及 Session/Audit 的工作依赖 M2。退出：进入 G3 文档与兼容阶段。

| Work ID | 工作 | 关键验收 |
|---|---|---|
| CON-001 | 从 Pydantic Model 生成 10 个 Tool Schema，统一错误 Envelope | `TC-CONTRACT-001–010` Pass |
| MEM-001 | `memory_store`/Tag/Query、content hash、source identity、mtime、import batch 和 λ 连续边界 | `TC-MEM-001–004`、`TC-MEM-007`、`TC-MEM-008`、`TC-MEM-010` Pass |
| MEM-002 | 默认关闭 startup import，提供固定 CLI/API delete、dry run 和迁移报告 | `TC-MEM-005`、`TC-MEM-006`、`TC-MEM-009`、`TC-MEM-011–013` Pass；Delete 缺 `--confirm` 时拒绝；不增加公共 Tool |
| PLAN-001 | 自依赖、缺失依赖、跨 Plan、循环、更新后校验和 Cascade 影响集合 | `TC-PLAN-003–007`、`TC-PLAN-009` Pass |
| PLAN-002 | 状态机、创建/更新事务和短任务重复步骤修复 | `TC-PLAN-001`、`TC-PLAN-002`、`TC-PLAN-008`、`TC-PLAN-010` Pass |
| PLAN-003 | 用 `plan_status` 承担公共 Query；增加固定 CLI/API Delete/Archive，禁止跨 Plan 删除 | `TC-PLAN-011–013` Pass；Delete 缺 `--confirm` 时拒绝；公共 Tool 仍为 10 个 |
| CP-001 | Plan/Completed ID 归属、并发编号、Review Rule Version | `TC-CP-001–006` Pass |
| AUD-001 | JSONL 事件源和 Markdown 派生报告 | `TC-POLICY-006–008` Pass |
| OPS-001 | 增加手工 `audit` 命令，将 Cron 降级为不自动安装的示例 | 新增 `TC-AUDIT-CLI-001`；安装/卸载不修改定时任务 |
| INTENT-001 | 修复低置信阈值、否定语义和用户显式优先 | `TC-INTENT-001–008` + 数据集指标 |

### 6.6 M4：开源可用性、兼容性与 Release Candidate

状态：未开始。

估算：8–13 人日。依赖：M2、M3。退出：G3。

| Work ID | 工作 | 关键验收 |
|---|---|---|
| DOC-001 | README 按 Stable/Beta/Experimental/Degraded/Removed 分级 | 每项主要能力链接到测试或运行证据 |
| DOC-002 | 安装、升级、Doctor、卸载、隐私、Troubleshooting、Known Limitations | 陌生用户无需源码知识即可操作 |
| QA-001 | `test-fast`、`test-integration`、`test-release` 三条测试通道 | 普通贡献者无需真实 API 即可跑 fast suite |
| QA-002 | Ruff、类型、ShellCheck、Coverage、依赖与 Secret 扫描 | CI Gate 全绿，豁免有期限和 Owner |
| COMPAT-001 | Linux/macOS、Python 3.10–3.12、真实 Hermes E2E | 支持矩阵与 package metadata 一致 |
| SEC-001 | SECURITY、第三方许可证、SBOM、发布权限最小化 | 安全审查清单完成 |
| MIG-001 | 完成从审查基线版本到 Beta 的 Config/DB/JSONL Migration、拒绝降级和失败回滚 | `TC-MIG-001–006` 通过，覆盖 `FR-INSTALL-004` 和 PRD §18[→附录 Q#8] |
| SEC-002 | Local API、文件权限、输入限制、Prompt Injection 边界和破坏性操作保护 | `TC-SERVER-005`、`TC-SEC-002–006` 通过 |
| REL-006 | Build/Publish/Rollback 自动化和 Release Checklist | RC 制品可重复构建并可撤回 |

### 6.7 M5：Public Beta 验证

状态：未开始。

日历周期：至少 14 天。依赖：G3。退出：G4。

| Work ID | 工作 | 关键验收 |
|---|---|---|
| BETA-001 | 发布 `v3.0.0-beta.1` 和不可变制品 | Tag、制品、SHA256、SBOM、provenance、Release Notes 一致 |
| BETA-002 | 按第 9 节招募、记录和计算外部验证指标 | 原始计数、环境、失败分类和 Wilson 区间可复算 |
| BETA-003 | 逐项分诊 Beta 失败并创建独立修复 Work ID/Issue，本任务不改业务代码 | P0 立即暂停；修复后重新过受影响 Gate，新版本递增预发布号 |
| REL-007 | 演练发布撤回、用户回滚和诊断通知 | 不覆盖 Tag/制品，回滚步骤由第三方复现 |

### 6.8 M6：Stable 候选

状态：未开始。

工程工作依赖 G4；发布授权为 G5。`REL-008` 只能在 G5 通过后执行。

| Work ID | 工作 | 关键验收 |
|---|---|---|
| STABLE-001 | 关闭所有 P1，清理所有 Beta Waiver | P0 = 0、P1 = 0 |
| SOAK-001 | 以最终 RC 重新执行 14 天稳定观察 | 达到第 9 节暴露量且无数据完整性 P0 |
| REL-008 | G5 通过后发布 `v3.0.0` | Tag、制品、文档和 Changelog 一致 |

### 6.9 总体工期判断

- M0–M4 净工程量：33–53 人日；Stable 关闭与发布另计 1–2 人日；
- 单维护者、有日常 Issue/PR 干扰时：大概率为 9–14 周；
- 上述估算不包含 Beta 新缺陷修复，也不把 M5/M6 各至少 14 天的观察期折算为工程人日；
- 估算置信度：大概率（70%），所有 Issue 完成细分后必须重新估算。[→附录 Q#6]

## 7. 已知缺陷追踪基线

以下 Work ID 是计划内稳定标识，不等同于 GitHub Issue 编号。每行首个 Work ID 是该缺陷的主责 Issue，其余为关联 Issue；M0 完成时必须补上真实 Issue 链接，后续再补 PR、Commit 和测试报告。P0/P1 的主责 Work ID 互不重复，因此不会由一个 Issue 同时承担两个 Release Blocker。

| Review ID | 责任 Work ID（首项为主责） | 测试证据 | Milestone | Gate |
|---|---|---|---|---|
| CR-P0-001 Server 安装/启动不成立 | PKG-001、PKG-002、RUN-001、RUN-002、INS-001–003 | XF-INSTALL-001；XF-PKG-001；TC-INSTALL-001–008；TC-SERVER-001–004 | M1 | G1 |
| CR-P0-002 Merge 重复尾消息 | CTX-001 | XF-CTX-001；TC-CTX-003 | M2 | G2 |
| CR-P0-003 Summary 失败丢历史 | CTX-002 | XF-CTX-002；TC-CTX-004、TC-CTX-005、TC-CTX-006 | M2 | G2 |
| CR-P0-004 硬约束未逐字保留 | CTX-003 | XF-CTX-003；TC-CTX-007、TC-CTX-008、TC-CTX-009 | M2 | G2 |
| CR-P0-005 跨 Session 污染 | SES-001 | XF-POLICY-001；TC-POLICY-001、TC-POLICY-004、TC-POLICY-005 | M2 | G2 |
| CR-P1-001 Tool Contract 不一致 | CON-001 | XF-CONTRACT-001–003；TC-CONTRACT-001–010 | M3 | G3 |
| CR-P1-002 Audit 格式不兼容 | AUD-001 | XF-AUDIT-001；TC-POLICY-008 | M3 | G3 |
| CR-P1-003 Cron 不可安装 | OPS-001 | TC-AUDIT-CLI-001（待新增） | M3 | G3 |
| CR-P1-004 Memory 导入不幂等 | MEM-002、MEM-001 | XF-MEM-001；TC-MEM-003–009 | M3 | G3 |
| CR-P1-005 DAG 实际为线性链 | PLAN-001、PLAN-002 | TC-PLAN-003–010 | M3 | G3 |
| CR-P1-006 Intent 低置信失效 | INTENT-001 | TC-INTENT-001–008 | M3 | G3 |
| CR-P1-007 外部摘要隐私未定义 | PRIV-001、DOC-002 | TC-CTX-010；TC-SEC-001 | M2/M4 | G2/G3 |
| CR-P2-001 Skill 学习名实不符 | DOC-001 | README 能力证据检查 | M4 | G3 |
| CR-P2-002 版本不一致 | REL-001 | XF-VERSION-001；版本一致性测试 | M0/M4 | G0/G3 |
| CR-P2-003 CI 仅有 pytest | QA-001、QA-002 | CI Required Checks | M4 | G3 |
| CR-P2-004 测试接触真实 HOME | QA-ART-001、QA-001 | HOME 隔离断言 | M1/M4 | G1/G3 |
| CR-P2-005 README 承诺过度 | DOC-001、DOC-002 | README 能力证据检查 | M4 | G3 |

### 7.1 当前 12 个 strict XFAIL 唯一索引

实施 AI 必须使用下表的精确 pytest node 复现目标缺陷。修复后删除该 node 上的 strict XFAIL 并保持断言强度；不得只修改 `XF-*` 文档状态。基线新增或减少 XFAIL 时，先由 `REL-003` 更新本表与追踪矩阵。

| XF ID | 精确 pytest node | 主责 Work ID |
|---|---|---|
| XF-CTX-001 | `tests/test_context_integrity_regressions.py::test_merge_path_does_not_duplicate_tail_messages` | CTX-001 |
| XF-CTX-002 | `tests/test_context_integrity_regressions.py::test_summary_failure_preserves_original_messages` | CTX-002 |
| XF-CTX-003 | `tests/test_context_integrity_regressions.py::test_hard_constraint_message_survives_verbatim` | CTX-003 |
| XF-POLICY-001 | `tests/test_release_readiness_regressions.py::test_hard_constraints_are_isolated_between_sessions` | SES-001 |
| XF-AUDIT-001 | `tests/test_release_readiness_regressions.py::test_immune_audit_parses_assessor_output_format` | AUD-001 |
| XF-CONTRACT-001 | `tests/test_release_readiness_regressions.py::test_memory_filter_tool_uses_api_contract` | CON-001 |
| XF-CONTRACT-002 | `tests/test_release_readiness_regressions.py::test_checkpoint_tool_schema_matches_api_required_fields` | CON-001 |
| XF-CONTRACT-003 | `tests/test_release_readiness_regressions.py::test_plan_status_schema_matches_service_enum` | CON-001 |
| XF-INSTALL-001 | `tests/test_release_readiness_regressions.py::test_install_script_installs_harness_server_runtime` | PKG-001 |
| XF-PKG-001 | `tests/test_release_readiness_regressions.py::test_runtime_dependencies_include_openai` | PKG-002 |
| XF-VERSION-001 | `tests/test_release_readiness_regressions.py::test_project_versions_are_consistent` | REL-001 |
| XF-MEM-001 | `tests/test_release_readiness_regressions.py::test_memory_import_storage_is_idempotent` | MEM-002 |

### 7.2 Test ID 唯一主责

#### 7.2.1 现有 83 个 Test ID

下表按无重叠集合分配现有测试计划的全部 83 个 Test ID。主责 Work ID 必须实现并维护对应测试；其他任务可运行它，但不得弱化断言或另建同义 Test ID。

| Test ID 集合 | 数量 | 主责 Work ID |
|---|---:|---|
| TC-INSTALL-001–003 | 3 | INS-001 |
| TC-INSTALL-004–005 | 2 | INS-002 |
| TC-INSTALL-006–008 | 3 | INS-003 |
| TC-POLICY-001–005 | 5 | SES-001 |
| TC-POLICY-006–008 | 3 | AUD-001 |
| TC-INTENT-001–008 | 8 | INTENT-001 |
| TC-CTX-001–002、TC-CTX-011–013 | 5 | CTX-004 |
| TC-CTX-003 | 1 | CTX-001 |
| TC-CTX-004–006 | 3 | CTX-002 |
| TC-CTX-007–009、TC-CTX-014 | 4 | CTX-003 |
| TC-CTX-010 | 1 | PRIV-001 |
| TC-CONTRACT-001–010 | 10 | CON-001 |
| TC-PLAN-003–007、TC-PLAN-009 | 6 | PLAN-001 |
| TC-PLAN-001–002、TC-PLAN-008、TC-PLAN-010 | 4 | PLAN-002 |
| TC-MEM-001–004、TC-MEM-007–008、TC-MEM-010 | 7 | MEM-001 |
| TC-MEM-005–006、TC-MEM-009 | 3 | MEM-002 |
| TC-CP-001–006 | 6 | CP-001 |
| TC-SERVER-001–003 | 3 | RUN-001 |
| TC-SERVER-004 | 1 | RUN-002 |
| TC-SERVER-005 | 1 | SEC-002 |
| TC-SEC-001 | 1 | PRIV-001 |
| TC-SEC-002–004 | 3 | SEC-002 |
| **合计** | **83** | 无重复、无遗漏 |

#### 7.2.2 G0 必须登记的 17 个新增 Test ID

这些 ID 是本计划新增范围的固定验收契约，当前测试计划尚未登记。`REL-000` 只把下列用例逐条写入 `docs/testing/TEST_PLAN.md`，不得在 M0 编写业务实现；相应 Work ID 实现测试。G0 未完成同步前，不得执行 M1 及以后任务。`REL-000` 还必须收紧既有用例：`TC-INSTALL-006`、`TC-INSTALL-007` 使用 §2.3 的 distribution/部署边界与 `--purge-data --confirm`，`TC-MEM-009` 要求 `--confirm`，`TC-SEC-004` 覆盖 symlink/path traversal，`TC-SERVER-001–005` 使用 §2.4 的探针/envelope；这些既有 ID 不重复计数。

| Test ID | 固定场景 | 固定期望 | 实现 Work ID |
|---|---|---|---|
| TC-INSTALL-009 | Python 或 Hermes 版本不在固定支持矩阵 | install/doctor 以非零退出，JSON 与人类输出均含检测值和支持范围 | INS-002 |
| TC-INSTALL-010 | 捕获 install/upgrade/uninstall 启动的所有子进程 | CLI 从不调用 pip；普通 uninstall 输出精确的 pip 卸载命令 | INS-003 |
| TC-PLAN-011 | 按 ID 查询 Plan、依赖图和更新时间 | 返回完整图；不存在时返回统一 not-found envelope | PLAN-003 |
| TC-PLAN-012 | Archive Plan 后执行默认 Query | 默认查询不返回；显式 include-archived 可返回；数据仍存在 | PLAN-003 |
| TC-PLAN-013 | 存在两个 Plan 时先无 `--confirm`、再确认删除其中一个 | 首次拒绝且无变化；确认后只删除目标 Plan，不影响另一 Plan | PLAN-003 |
| TC-MEM-011 | 使用默认配置启动三次 | 不扫描或导入用户 Memory 文件 | MEM-002 |
| TC-MEM-012 | 对可导入文件执行 dry run | 输出逐文件新增/更新/跳过/错误数，DB 字节与行数均不变 | MEM-002 |
| TC-MEM-013 | 参数化损坏 UTF-8、截断和取消 | 错误/截断/取消可诊断，当前文件不产生半批次写入 | MEM-002 |
| TC-AUDIT-CLI-001 | 手工执行 `deepseek-harness audit`，并比较前后 scheduler 状态 | 报告可生成；install/uninstall 均不修改 crontab/systemd/launchd | OPS-001 |
| TC-SEC-005 | 安装后检查运行目录和文件权限 | 目录 `0700`，配置/DB/事件/日志/runtime 文件 `0600` | SEC-002 |
| TC-SEC-006 | Summary 含历史指令或 Prompt Injection，随后请求破坏性操作 | 摘要仅作参考材料，不提升权限、不绕过显式 `--confirm` | SEC-002 |
| TC-MIG-001 | 从 `develop@37e4016` fixture 执行完整升级 | 备份后 Config、DB、事件和进程状态迁移成功，Doctor 全绿 | MIG-001 |
| TC-MIG-002 | 对重复 Memory 先 dry run 再执行迁移两次 | dry-run 不写入；重复迁移不新增重复数据 | MIG-001 |
| TC-MIG-003 | 迁移 Markdown 约束日志，包含不可解析条目 | 合法事件进入 JSONL；不可解析内容保留在原文件并报告 | MIG-001 |
| TC-MIG-004 | 旧 Server 正在运行时升级 | 先停止旧进程，再安装新 package；不存在双进程 | MIG-001 |
| TC-MIG-005 | 在备份、DB、Config、安装、Doctor 各阶段注入失败 | 每个阶段均恢复原配置、DB 和可运行旧版本 | MIG-001 |
| TC-MIG-006 | 旧程序读取新 Schema，或请求无迁移路径的降级 | 启动前拒绝并给出恢复命令，不修改数据 | MIG-001 |

### 7.3 全部 88 个功能需求覆盖

下表覆盖 PRD 中全部 88 个 `FR-*`。`REL-003` 的实施内容不再是重新设计映射，而是经用户明确授权后为 48 个 Work ID 创建 GitHub Issue，并把真实 Issue 链接回本表；未经授权必须停在 G0，不得用本地占位链接冒充完成。PR、Commit 和最终测试报告在各 Work ID 交付后继续回填。

| 需求域 | 数量 | Work ID | 测试范围 | Release Gate |
|---|---:|---|---|---|
| FR-INSTALL-001–006 | 6 | INS-001–003、QA-ART-001、MIG-001 | TC-INSTALL-001–010、TC-MIG-001–006 | G1/G3/G5 |
| FR-PLUGIN-001–005 | 5 | PKG-001、INS-001、INS-003、COMPAT-001 | Plugin Registration、Lifecycle E2E | G1/G3 |
| FR-POLICY-001–008 | 8 | SES-001、AUD-001、OPS-001 | TC-POLICY-001–008、TC-AUDIT-CLI-001 | G2/G3 |
| FR-INTENT-001–007 | 7 | INTENT-001、DOC-001 | TC-INTENT-001–008 + 数据集指标 | G3 |
| FR-CONTEXT-001–013 | 13 | CTX-001–004、PRIV-001 | TC-CTX-001–014、Property Test | G2 |
| FR-SERVER-001–007 | 7 | PKG-001、RUN-001、RUN-002、CON-001、SEC-002 | TC-SERVER-001–005、Process E2E | G1/G3 |
| FR-PLAN-001–008 | 8 | CON-001、PLAN-001–003 | TC-PLAN-001–013 | G3 |
| FR-MEMORY-001–007 | 7 | CON-001、MEM-001、MEM-002 | TC-MEM-001–013 | G3 |
| FR-CHECKPOINT-001–006 | 6 | CON-001、CP-001 | TC-CP-001–006 | G3 |
| FR-OBS-001–005 | 5 | RUN-002、AUD-001、PRIV-001、DOC-002 | 日志 Schema、Redaction、Runtime Status | G2/G3 |
| FR-SEC-001–007 | 7 | PRIV-001、SEC-001、SEC-002、INS-001、INS-003 | TC-SEC-001–006 + 依赖/权限审查 | G2/G3 |
| FR-QA-001–009 | 9 | QA-ART-001、QA-001、QA-002、COMPAT-001、REL-006 | Fast/Integration/Release CI | G1/G3 |
| **合计** | **88** | 无未映射需求 | `REL-003` 补真实链接 | — |

任何新增 Requirement 必须先进入本表并分配 Work ID，之后才能实现；不得先写代码再补需求编号。

## 8. Issue 与 Definition of Done

每个执行 Issue 必须包含：

- Work ID、Requirement ID、CR/XF ID 和优先级；
- 当前行为、期望行为和最小复现；
- 方案假设及其源码/测试依据；
- 明确 Owner、估算和前置依赖；
- 自动验收测试及失败输出；
- 配置、数据、隐私和兼容性影响；
- Upgrade/Rollback 说明；
- 文档改动；
- 不在范围内的事项。

Issue 粒度固定为“一个 Work ID 一个执行 Issue”。同一 Issue 不得实现多个 Work ID；同一 Work ID 也不得拆成多个可独立关闭的实现 Issue。若任务确实过大，必须先修订本计划和追踪矩阵再拆分，不允许实施 AI 临场改变粒度。

一个 Issue 只有同时满足以下条件才可关闭：

1. 最小实现已合入；
2. 正常、边界和故障测试通过；
3. strict XFAIL 已删除并转为永久回归测试；
4. 不读取或修改真实 HOME；
5. 对应文档和配置已更新；
6. Required CI Checks 全绿；
7. Requirement → Test → PR 追踪完成；
8. 无新增未披露数据发送；
9. 对外文案与实际能力一致。

## 9. Beta 验证指标

### 9.1 操作定义

- **独立安装尝试**：从干净环境和不可变 Beta 制品开始，完成安装、Doctor、至少一个 Tool Smoke Test 和普通卸载；同一环境的重复重试不增加分母。
- **安装成功**：上述四步全部成功，且无需维护者直接修改用户环境。
- **文档自助成功**：用户只依据公开文档完成安装；允许查询文档，不允许维护者同步远程操作。
- **长会话**：至少 20 个 user/assistant turn 或至少 10 个合法 Tool 调用，并至少触发一次 Context 压缩尝试。
- **合法 Tool 调用**：输入满足注册 Schema 且 Server 已 ready。5xx、超时、无效响应 Envelope 计为产品失败；Schema 拒绝和用户取消单独报告。
- **数据损坏**：消息缺失、重复、顺序错误、Tool Pair 破坏、错误 Memory 写入或不可恢复迁移。

### 9.2 最小样本与阈值

| 指标 | 最小样本 | Gate |
|---|---:|---|
| 外部验证者 | 10 名非维护者 | 覆盖 Linux/macOS 和支持 Python 版本 |
| 独立安装尝试 | 20 次 | 观察成功率 ≥ 90%；同时报告 95% Wilson 区间 |
| 文档自助安装 | 10 人 | 成功率 ≥ 80% |
| 长会话 | 50 次 | 0 个确认的数据损坏或跨 Session 污染 |
| 合法 Tool 调用 | 200 次 | 总成功率 ≥ 95%，每个 Tool ≥ 10 次且成功率 ≥ 90% |
| Context 压缩尝试 | 50 次 | 每次均满足完整性检查或完整 rollback |

这些数据用于 Beta 可用性判断，不得宣称为生产级可靠性统计。[→附录 Q#5]

### 9.3 隐私约束

- 默认不上传遥测；
- 不收集 Prompt 原文、完整 Tool 参数、完整 Tool Result、Secret 或用户文件；
- 只使用用户主动提交的结构化诊断包；
- 诊断包必须支持预览和再次脱敏；
- 每个指标必须保留分子、分母、环境和失败分类，不只记录百分比。

## 10. CI 与验证通道

### `test-fast`

面向普通 PR，目标 30 分钟内完成：

- Unit、Contract、临时 SQLite；
- Ruff、格式和类型检查；
- Fake Provider；
- 不访问网络和真实 HOME。

### `test-integration`

- 真实 Server 子进程；
- App Factory、端口占用、DB lock；
- wheel 安装后的 Tool/API Contract；
- pip install → install → doctor → smoke → 普通 uninstall → pip uninstall 的临时 HOME E2E。

### `test-release`

- 从干净 Tag 构建并安装最终制品；
- Linux/macOS、Python 3.10–3.12；
- 真实 Hermes 正式版本；
- 受控 DeepSeek API Smoke Test；
- Upgrade、Migration、Rollback；
- 依赖、Secret、许可证、SBOM 和制品完整性检查。

只有 `test-release` 可以为 Release Gate 提供最终制品证据；源码目录中的 `pytest` 结果不能替代它。

## 11. 发布与回滚流程

1. 从通过 G3 的 `develop` 创建 RC PR 到 `master`；
2. 冻结版本、依赖锁定范围和 Migration；
3. 从目标 Commit 的干净快照构建制品；
4. 对制品执行完整 `test-release`；
5. 生成 SHA256、SBOM、GitHub Artifact Attestation、Release Notes、Known Limitations 和测试报告；
6. 创建不可变预发布 Tag 和 GitHub Release；
7. 完成 G4 外部验证；
8. 若出现 P0，立即停止推广、标记受影响版本、发布诊断与回滚说明；
9. 禁止覆盖已有 Tag 或替换同名制品；修复必须发布新预发布号；
10. Stable 仅在 G5 通过后发布。

普通卸载默认保留 Python distribution 和用户数据。`uninstall --purge-data` 必须列出精确路径并要求 `--confirm`，且通过 symlink/path traversal 测试；最后由用户或 Release Test 显式运行 pip uninstall。

## 12. 风险登记

| 风险 | 概率/影响 | 预警证据 | 缓解与停止条件 |
|---|---|---|---|
| wheel 构建成功但不可运行 | 已发生 / P0 | 制品缺 Server、配置和可导入包 | G1 强制源码外制品 E2E |
| Context 修复引入新消息损坏 | 高 / P0 | Property Test 或回归失败 | 保持 rollback-first；任何失败阻断 G2 |
| Hermes 内部接口不兼容 | 高 / P0 | 真实 E2E Hook/Tool 失败 | Beta 固定单一 Hermes 版本，不扩大承诺 |
| 外部摘要泄露敏感数据 | 中高 / P0 | Redaction/Audit 失败 | 默认可关闭；失败阻断 G2 |
| 单维护者工期失真 | 高 / P1 | Issue 无估算、WIP 超限 | 每次只推进一个 P0 域；Gate 优先于日期 |
| Beta 样本过少造成错误稳定结论 | 高 / P1 | 未达到第 9 节暴露量 | 不发布 Stable，不用“无报告”代替证据 |
| P1 Waiver 长期存在 | 中 / P1 | Waiver 到期或无 Owner | 到期自动阻断下一 Beta；Stable 不接受 Waiver |

## 13. 资源分配

单维护者默认分配：

- 60%：当前 Gate 的 P0/P1 实现与回归；
- 20%：制品、CI 和测试隔离；
- 10%：安装、Doctor、文档；
- 10%：Issue/PR、Release 和外部验证维护；
- 0%：新增 Innovation 和非目标平台。

WIP 限制：同一时间最多一个 P0 域处于实现状态，最多一个独立测试/文档 Issue 并行。外部贡献者优先承担 Contract Test、文档真实性、Test Isolation、Doctor 检查和 Memory 幂等测试；Context Integrity、Session State、Migration 和 Release 权限由核心维护者审查。

## 14. 明确不做

`v3.0.0` 前不做：

- I-19 及以后 Innovation；
- Claude Code、Codex、OpenCode 适配；
- Web UI / Desktop UI；
- 多 Agent 编排平台；
- 云 Memory、账号、OAuth/RBAC、多租户；
- 分布式服务；
- 自动执行或自动生成复杂 Skill；
- LLM 自动生成复杂 DAG；
- 商业化功能。

## 15. 成功定义

项目达到开源 Stable 的标志是：

> 一个陌生用户能从不可变发布制品安装、完成任务、诊断故障并安全卸载；一个陌生贡献者能复现问题、运行分层测试并提交可追踪的修改；维护者能用自动化 Gate 判断发布或回滚，而不依赖宣传文案和主观信心。

---

## 附录 A：Work ID 施工索引

§6 定义“做什么和先后顺序”，本附录定义“允许改哪里、必须怎样证明”。本列路径均相对仓库根，`**` 表示该目录后代；没有反引号包裹的项目必须明确标为外部资源。`PKG-001` 之前使用现有路径；`PKG-001` 完成后，业务源码路径一律切换到 §3.7 的 `src/` 布局。

除每行列出的路径外，所有 Work ID 均可新增或更新 `docs/testing/evidence/<WORK-ID>.md`，并更新 `docs/traceability/RELEASE_TRACEABILITY.md` 中自己的记录；这项通用例外不授权修改其他业务文件。只有 Gate 协调者可新增 `docs/testing/evidence/GATE-G<N>.md` 并更新本计划中的 Gate 状态，普通实施 AI 只提交证据链接。

### A.1 M0 施工索引

| Work ID | 允许修改/新增 | 必须验证 | 完成证据 |
|---|---|---|---|
| REL-000 | `docs/product/PRD.md`、`docs/architecture/PRODUCT_ARCHITECTURE.md`、`docs/architecture/TECHNICAL_ARCHITECTURE.md`、`docs/testing/TEST_PLAN.md`、`docs/README.md` | `v3.0.0-beta.1`、10 Tool、安全默认值、运行路径、CLI、Python/OS 范围与本计划一致；§7.2.2 的 17 个 Test ID 逐条进入测试计划；不改业务代码 | 逐项口径对照表 + 100 个 Test ID 唯一性/主责检查 + `rg` 冲突搜索为 0 |
| REL-001 | `pyproject.toml`、`plugins/deepseek-harness/plugin.yaml`、`plugins/deepseek-context/plugin.yaml`、`CHANGELOG.md`、`README.md`、`README_EN.md`、`docs/README.md`、`tests/test_release_readiness_regressions.py`、`docs/decisions/VERSIONING.md` | `test_project_versions_are_consistent` 取消 XFAIL并通过；`requires-python` 与矩阵一致 | 版本 ADR + 三处版本映射 + 测试输出 |
| REL-002 | `CONTRIBUTING.md`、`docs/README.md`、`docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md`、`.github/pull_request_template.md`、`docs/contributing/BRANCH_POLICY.md`；外部资源：GitHub Repository Settings（需用户明确授权） | `rg` 不再出现要求业务 PR 直接进入 `master` 的冲突规则；默认分支为 `develop`；两保护分支禁止强推/删除、要求 PR 和当前 CI | 分支规则对照表 + 脱敏后的 GitHub Settings/Ruleset 查询结果；未获外部写入权限则不得关闭 |
| REL-003 | `docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md`、`docs/traceability/RELEASE_TRACEABILITY.md`；外部资源：GitHub Issues（需用户明确授权） | 88 个 FR、17 个 CR、48 个 Work ID 无孤儿；每个 Work ID 有唯一 Issue；P0/P1 主责与关联链接完整 | 机器可检索矩阵；真实 Issue URL；缺失计数为 0；未获外部写入权限则不得关闭 |
| REL-004 | `plugins/deepseek-harness/plugin.yaml`、`plugins/deepseek-context/plugin.yaml`、`plugins/deepseek-harness/tools.py`、`docs/product/PRD.md`、`docs/testing/TEST_PLAN.md`、`README.md`、`README_EN.md`、`tests/test_tool_registration.py`、`tests/test_release_readiness_regressions.py` | 当前 9、目标 10 的迁移说明明确；目标清单只能来自单一常量/Schema | 10 个名称排序后的断言输出 |
| REL-005 | `docs/release/PUBLISHING.md`、`docs/release/RELEASE_CHECKLIST.md`；外部资源：PyPI/GitHub Publisher Settings（需用户明确授权） | 只记录 PyPI 名称/Owner/2FA/Trusted Publisher 状态，不记录凭证 | 可用则发布前置清单；不可用则 GitHub-only 决策 |
| COMPAT-000 | `docs/compatibility/HERMES_MATRIX.md`、`tests/compatibility/probes/**`、`tests/fixtures/hermes/**` | 记录 Hermes Release、安装来源、Plugin/Context/Tool 接口和复现命令 | 一个明确候选版本 + E2E 方案；不声称已兼容 |
| GOV-001 | `SECURITY.md`、`.github/ISSUE_TEMPLATE/*`、`.github/pull_request_template.md`、`docs/release/RELEASE_CHECKLIST.md` | 模板包含 Work/Requirement/Test/风险/回滚字段；Security 有私密报告渠道和响应范围 | 模板渲染检查 + 文件链接检查 |

### A.2 M1 施工索引

| Work ID | 允许修改/新增 | 必须验证 | 完成证据 |
|---|---|---|---|
| PKG-001 | `pyproject.toml`、`src/deepseek_harness/**`、`src/deepseek_context/**`、`src/harness_server/**`、`plugins/deepseek-harness/**`、`plugins/deepseek-context/**`、`mcp/harness_server/**`、`tests/conftest.py`、`tests/test_package_artifact.py` | 从 `git archive` 构建 wheel；源码外 import 三个 package；wheel 含四个 YAML/resource；无重复业务源码 | wheel 文件清单、三个 import 路径、目标测试输出 |
| PKG-002 | `pyproject.toml`、`src/deepseek_context/**`、`src/harness_server/**`、`tests/test_package_dependencies.py`、`tests/test_release_readiness_regressions.py` | clean venv 分别安装 base/context/server/all；每个 extra 只承诺其能力；实际 import 无缺依赖 | 四个 clean-install 结果 + metadata 检查 |
| RUN-001 | `src/harness_server/app.py`、`src/harness_server/config.py`、`src/harness_server/server.py`、`src/harness_server/models.py`、`src/deepseek_harness/tools.py`、`tests/test_harness_server.py`、`tests/test_server_process.py` | import 不创建 DB/导入 Memory；App Factory 可注入 tmp DB；health/ready/version 行为分离；Plugin/CLI/Server 共用 `HARNESS_HOST`/`HARNESS_PORT`；旧同义变量引用为 0 | 子进程 readiness、环境变量矩阵与故障注入日志 |
| RUN-002 | `src/harness_server/supervisor.py`、`src/harness_server/runtime.py`、`src/deepseek_harness/cli.py`、`tests/test_server_process.py` | start 两次只有一个进程；status 校验 PID 与端口；stop 幂等；stderr 可诊断 | PID/state/log 样例 + Process E2E |
| INS-001 | `src/deepseek_harness/cli.py`、`src/deepseek_harness/installer.py`、`src/deepseek_harness/resources/**`、`scripts/install.sh`、`tests/test_installer_e2e.py` | TC-INSTALL-001–003；dry-run 无持久变化；clean install 完整；重复安装无重复配置/进程 | 临时 HOME 前后文件快照 + 重复安装结果 |
| INS-002 | `src/deepseek_harness/cli.py`、`src/deepseek_harness/doctor.py`、`tests/test_installer_e2e.py` | TC-INSTALL-004、TC-INSTALL-005、TC-INSTALL-009；缺依赖、版本不支持、端口占用均给出错误码和恢复建议 | Doctor JSON/人类可读输出 + 故障注入结果 |
| INS-003 | `src/deepseek_harness/cli.py`、`src/deepseek_harness/installer.py`、`src/deepseek_harness/migration.py`、`tests/test_installer_e2e.py`、`tests/fixtures/migration/**` | TC-INSTALL-006–008、TC-INSTALL-010；普通卸载保留 distribution/数据；`--purge-data --confirm` 拒绝越界路径；安装中断可重试；CLI 不调用 pip | 旧版 fixture、子进程捕获、文件快照、回滚与卸载报告 |
| QA-ART-001 | `tests/test_package_artifact.py`、`scripts/test_artifact.sh`、`.github/workflows/ci.yml` | CI 测试只安装 wheel；临时目录离开 repo 后仍能 CLI → Server → Tool Smoke → 普通 uninstall → pip uninstall | CI Artifact/JUnit + wheel SHA256 |

### A.3 M2 施工索引

| Work ID | 允许修改/新增 | 必须验证 | 完成证据 |
|---|---|---|---|
| CTX-001 | `src/deepseek_context/**`、`tests/test_context_integrity_regressions.py` | `test_merge_path_does_not_duplicate_tail_messages` 删除 XFAIL并通过；每个 Tail ID 恰好一次 | 修复前 XFAIL、修复后 Pass 对比 |
| CTX-002 | `src/deepseek_context/**`、`tests/test_context_integrity_regressions.py` | `test_summary_failure_preserves_original_messages` 删除 XFAIL；None、异常、超时、缺 Key 均返回原消息 | 四类故障参数化测试 |
| CTX-003 | `src/deepseek_context/**`、`tests/test_context_integrity_regressions.py`、`tests/test_context_properties.py` | 受保护原文、唯一 ID、最新请求一次、Tool Pair 合法；原 XFAIL 转 Pass | 固定回归 + Hypothesis 最小反例为 0 |
| CTX-004 | `src/deepseek_context/**`、`tests/test_context_engine.py`、`tests/test_context_properties.py` | 阈值以下不压缩；正常摘要减少 Token；Token 不降 rollback；输入深拷贝不变；不同 Session summary state 不共享 | TC-CTX-001、TC-CTX-002、TC-CTX-011–013 + 输入前后序列化对比 |
| SES-001 | `src/deepseek_harness/session_policy.py`、`src/deepseek_harness/gate.py`、`src/deepseek_harness/assessor.py`、`tests/test_gate_v2.py`、`tests/test_assessor_v2.py`、`tests/test_session_policy.py`、`tests/test_release_readiness_regressions.py` | `test_hard_constraints_are_isolated_between_sessions` 转 Pass；并发、取消约束、end cleanup 通过 | 两线程屏障测试 + Store 生命周期日志 |
| PRIV-001 | `src/deepseek_context/**`、`src/deepseek_harness/immune_audit.py`、`tests/test_context_privacy.py`、`tests/test_context_integrity_regressions.py` | Secret 在外发与日志均不存在；Summary 可关闭；诊断事件不含原 Prompt | Fake Provider 捕获请求 + 日志扫描 |

### A.4 M3 施工索引

| Work ID | 允许修改/新增 | 必须验证 | 完成证据 |
|---|---|---|---|
| CON-001 | `src/harness_server/models.py`、`src/harness_server/app.py`、`src/harness_server/server.py`、`src/harness_server/schema.py`、`src/deepseek_harness/tools.py`、`tests/test_tool_registration.py`、`tests/test_tool_contract.py`、`tests/test_release_readiness_regressions.py` | 三个现有 Contract XFAIL 转 Pass；10 个 Tool 最小合法 payload 均不返回 422；错误 Envelope 统一 | Schema 快照 + 10 个端到端响应 |
| MEM-001 | `src/harness_server/models.py`、`src/harness_server/storage.py`、`src/harness_server/server.py`、`tests/test_memory.py`、`tests/fixtures/memory/**` | content hash + source identity 唯一；λ 边界连续；Tag/Store/Query 正确；10k 性能目标通过 | TC-MEM-001–004、TC-MEM-007、TC-MEM-008、TC-MEM-010、DB 行数/唯一索引和 P95 报告 |
| MEM-002 | `src/harness_server/models.py`、`src/harness_server/storage.py`、`src/harness_server/server.py`、`src/deepseek_harness/cli.py`、`tests/test_memory.py`、`tests/test_release_readiness_regressions.py`、`tests/fixtures/memory/**` | `test_memory_import_storage_is_idempotent` 转 Pass；startup import 默认关闭；dry-run 不写 DB；delete 只影响目标 source；损坏 UTF-8/截断/取消可诊断且无半批次 | TC-MEM-005、TC-MEM-006、TC-MEM-009、TC-MEM-011–013、DB 前后快照和删除范围断言 |
| PLAN-001 | `src/harness_server/models.py`、`src/harness_server/storage.py`、`src/harness_server/server.py`、`tests/test_plan.py` | 自依赖、缺失、跨 Plan、创建/更新成环均拒绝且事务 rollback；Cascade 影响集合/原因正确且不静默改 Completed | TC-PLAN-003–007、TC-PLAN-009；每类非法图的 DB 前后快照 |
| PLAN-002 | `src/harness_server/models.py`、`src/harness_server/storage.py`、`src/harness_server/server.py`、`tests/test_plan.py` | 非法状态转换拒绝；Create/Update 原子；短任务不复制成三个相同步骤 | 状态转移参数化测试 + 唯一步骤断言 |
| PLAN-003 | `src/harness_server/models.py`、`src/harness_server/storage.py`、`src/harness_server/server.py`、`src/deepseek_harness/cli.py`、`src/deepseek_harness/tools.py`、`tests/test_plan.py` | 公共 Query 复用 `plan_status`；默认 Archive；Delete 需 `--confirm`；只删除目标 Plan；不新增 Tool | TC-PLAN-011–013 全部通过 |
| CP-001 | `src/harness_server/models.py`、`src/harness_server/storage.py`、`src/harness_server/server.py`、`tests/test_checkpoint.py` | Plan 存在、Completed ID 归属、并发编号唯一、规则版本幂等、Chain 有序 | 并发 barrier 测试 + 唯一约束证据 |
| AUD-001 | `src/deepseek_harness/assessor.py`、`src/deepseek_harness/immune_audit.py`、`src/deepseek_harness/audit_events.py`、`tests/test_assessor_v2.py`、`tests/test_audit.py`、`tests/test_release_readiness_regressions.py` | `test_immune_audit_parses_assessor_output_format` 转 Pass；JSONL 是唯一事实源，Markdown 只派生 | JSONL round-trip + 损坏行降级测试 |
| OPS-001 | `src/deepseek_harness/cli.py`、`src/deepseek_harness/immune_audit.py`、`crons/**`、`README.md`、`README_EN.md`、`tests/test_audit.py`、`tests/test_installer_e2e.py` | 手工 audit 可执行；install/uninstall 不改 crontab/launchd；示例不含绝对用户路径 | `TC-AUDIT-CLI-001` + 定时任务前后快照 |
| INTENT-001 | `src/deepseek_harness/intent_router.py`、`src/deepseek_harness/resources/strategies.yaml`、`tests/test_intent_router.py`、`tests/fixtures/intent/**` | 低置信路径可达；否定表达不误判；用户显式分类优先；输出 confusion matrix/macro F1 | 数据集版本 + 指标报告 + 回归测试 |

### A.5 M4 施工索引

| Work ID | 允许修改/新增 | 必须验证 | 完成证据 |
|---|---|---|---|
| DOC-001 | `README.md`、`README_EN.md`、`docs/capabilities/**`、`tests/test_docs.py` | 禁用“唯一/零副作用/永不冲突”等绝对化文案；每项能力有状态和证据链接 | 中英文能力表 + 链接检查 |
| DOC-002 | `README.md`、`README_EN.md`、`docs/guides/**`、`docs/release/KNOWN_LIMITATIONS.md`、`tests/test_docs.py`、`scripts/test_docs.sh` | 安装、升级、Doctor、卸载、隐私、Troubleshooting、Known Limitations 命令由 CI 抽取并执行或静态校验；不引用源码安装捷径 | 文档测试报告 + 新用户演练脚本 |
| QA-001 | `Makefile`、`scripts/test_fast.sh`、`scripts/test_integration.sh`、`scripts/test_release.sh`、`pyproject.toml` 中 pytest marker 配置、`.github/workflows/ci.yml` | `make test-fast`、`make test-integration`、`make test-release` 均存在；fast 无网络/真实 HOME；各层无重复收集 | 三条命令的用例清单和时长 |
| QA-002 | `pyproject.toml`、`.github/workflows/ci.yml`、`.github/workflows/release.yml`、`scripts/quality/**` | Ruff、格式、类型、ShellCheck、Coverage、pip-audit、Secret Scan 全部 Required | Required Checks 列表 + 有期 Waiver（如有） |
| COMPAT-001 | `.github/workflows/ci.yml`、`.github/workflows/release.yml`、`src/deepseek_harness/adapters/**`、`src/deepseek_context/adapters/**`、`tests/compatibility/**`、`tests/fixtures/hermes/**`、`docs/compatibility/HERMES_MATRIX.md` | Linux/macOS、Python 3.10–3.12；固定 Hermes 的 Hook/Context/10 Tool E2E | 每个支持单元的环境与结果 |
| SEC-001 | `SECURITY.md`、`scripts/security/**`、`.github/workflows/release.yml`、`docs/release/RELEASE_CHECKLIST.md` | 第三方许可证可追溯；SBOM 对应 wheel；发布权限使用最小化/OIDC 优先 | 安全清单 + SBOM + 权限说明 |
| MIG-001 | `src/deepseek_harness/migration.py`、`src/deepseek_harness/cli.py`、`src/harness_server/storage.py`、`tests/test_migration.py`、`tests/fixtures/migration/**` | 从当前版本成功迁移；中途失败恢复原版本；低版本程序拒绝新 Schema；覆盖 PRD §18 | TC-MIG-001–006、每个 fixture 的迁移/回滚结果和数据前后清单 |
| SEC-002 | `src/deepseek_harness/installer.py`、`src/deepseek_harness/cli.py`、`src/harness_server/**`、`src/deepseek_context/**`、`tests/test_security.py`、`tests/test_installer_e2e.py`、`tests/test_server_process.py` | 非 loopback 默认拒绝；文件权限最小；输入长度限制；Prompt 不提升 Tool 权限；`--purge-data` 防 symlink/traversal | TC-SERVER-005、TC-SEC-002–006 输出 |
| REL-006 | `.github/workflows/release.yml`、`scripts/release/**`、`docs/release/RELEASE_CHECKLIST.md` | 同 Commit 两次构建内容可解释；生成 GitHub Artifact Attestation；Test Release 不覆盖 Tag；失败不发布半套制品 | Dry-run Release 记录 + provenance 验证 + 撤回演练 |

### A.6 M5/M6 施工索引

| Work ID | 允许修改/新增 | 必须验证 | 完成证据 |
|---|---|---|---|
| BETA-001 | `.github/workflows/release.yml`、`docs/release/RELEASE_NOTES_v3.0.0-beta.1.md`、`docs/testing/reports/**`；外部资源：Git Tag/GitHub Release/可选 PyPI（需用户明确授权） | G3 全绿且制品来自同一 Commit | Tag、SHA256、SBOM、provenance、Run ID |
| BETA-002 | `docs/beta/METRICS_SCHEMA.md`、`docs/beta/VALIDATION_LOG.csv`、`docs/beta/VALIDATION_REPORT.md` | 第 9 节所有分子/分母可复算；重复尝试不重复计数；不得保存 Prompt 原文 | 去标识原始计数 + 指标报告 |
| BETA-003 | `docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md`、`docs/beta/FAILURE_LEDGER.md`、`docs/release/RELEASE_NOTES_*.md`；外部资源：GitHub Issues（需用户明确授权） | 每个失败有分类、Owner 和独立 Work ID/Issue；不改业务源码/测试；P0 触发暂停；修复后重新过受影响 Gate | 失败台账 + 新追踪链接 + Gate 状态 |
| REL-007 | `docs/release/ROLLBACK.md`、`scripts/release/rollback_drill.sh`、`docs/testing/reports/**` | 第三方从已发布 Beta 回滚且数据保留 | 演练时间线 + 验证结果 |
| STABLE-001 | `docs/beta/FAILURE_LEDGER.md`、`docs/release/RELEASE_CHECKLIST.md`；外部资源：GitHub Issues/Waivers（只读验证） | 开放 P0/P1 查询结果均为 0 | 可复现查询和关闭证据 |
| SOAK-001 | `docs/beta/SOAK_REPORT.md` | 最终 RC 连续 14 天达到暴露量；中途改代码重新计时；不修改业务代码 | 起止 Commit、日期和暴露量 |
| REL-008 | `.github/workflows/release.yml`、`CHANGELOG.md`、`README.md`、`README_EN.md`、`pyproject.toml`、`src/deepseek_harness/resources/plugin.yaml`、`src/deepseek_context/resources/plugin.yaml`、`docs/release/**`；外部资源：Git Tag/GitHub Release/可选 PyPI（需用户明确授权） | 执行前 G5 全绿；Tag/制品/文档一致；Beta 标记移除 | `v3.0.0` Release 证据包 |

### A.7 可直接交给实施 AI 的任务模板

复制以下模板，一次只替换一个 Work ID：

```text
只实施 docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md 中的 <WORK-ID>。

强制要求：
1. 先完整阅读 §1–§8、§10–§12 和附录 A 中 <WORK-ID> 对应行；M5/M6 任务还要阅读 §9。
2. 检查硬依赖是否完成；未完成则停止，不得提前实现。
3. 检查进行中 Issue 的允许路径；有交集则等待，不得并行修改。
4. 修改前写出一个可证伪假设，并引用源码/测试证据。
5. 只修改该 Work ID 允许的文件；需要越界时停止并报告。
6. 先运行基线测试，再做最小修改；禁止顺手重构。
7. strict XFAIL 修复后删除标记，禁止 skip、弱化断言或重试掩盖。
8. 使用临时 HOME、DB、端口和 Fake Secret；不得访问真实用户数据。
9. 完成文件层、集成层、管线层三层验证。
10. 按 §3.6 格式交付；任何测试未运行都必须写明原因，不能写“应该通过”。
11. 未经明确授权不发布、不推送、不创建外部资源。
```

## 附录 B：讨论债务

| ID | 未决事项 | Owner | 最迟决策点 | 阻断 |
|---|---|---|---|---|
| D-001 | PyPI 名称是否可用、维护者权限是否完备 | 核心维护者 | G0 | PyPI 发布，不阻断 GitHub Beta 制品 |
| D-002 | Beta 固定支持的 Hermes 正式版本 | 核心维护者 | G0 | G3 |

## 附录 C：审查问答记录

#### Q#1：为什么不再回退到 `v0.3.0-beta`？

> 2026-07-27 | 严格计划审查 | 版本升级语义

**问题**：当前根项目已经是 `2.0.0`，同一发行身份发布 `0.3.0` 会被包管理器视为旧版本，也无法表达升级关系。

**答案**：保留同一发行身份，因 package/安装契约存在破坏性变化，下一版本使用 `v3.0.0-beta.1`。只有新建 distribution 时才允许从 `0.x` 开始。

> [→ 正文 §2.1 已体现]

#### Q#2：为什么 Clean install 还不够？

> 2026-07-27 | 干净 Git 制品验证 | Artifact Gate

**问题**：当前仓库能构建并安装 wheel，但制品缺少 Server、配置、命令入口和可导入的下划线包。

**答案**：Release Gate 必须从干净 Tag 构建最终制品，并在源码目录外安装和运行。源码 checkout 或 editable install 不构成发布证据。

> [→ 正文 §2.2、§5 G1、§10 已体现]

#### Q#3：Tool 到底是 9 个还是 10 个？

> 2026-07-27 | 严格计划审查 | Contract 分母

**问题**：当前实现注册 9 个 Tool，但目标又新增 `memory_store`，原计划仍声称“九个 Tool Contract”。

**答案**：Beta 目标固定为 10 个公共 Tool；Contract 100% 的分母为本计划 §2.4 的清单。

> [→ 正文 §2.4 已体现]

#### Q#4：为什么继续使用 `develop`？

> 2026-07-27 | 仓库分支核对 | 稳定化期间集成策略

**问题**：远端默认分支和 CONTRIBUTING 当前使用 `master`，但审查、测试和修复基线已落在 `develop`。

**答案**：本发布周期以 `develop` 作为 GitHub 默认与唯一集成分支，并用 Ruleset 强制 PR；`master` 只接收通过 G3 的 RC，避免绕过当前验证基线。

> [→ 正文 §2.6 已体现]

#### Q#5：为什么不再使用“5 人、20 会话、无报告”作为 Beta 证明？

> 2026-07-27 | 严格计划审查 | 指标可测性

**问题**：5 人样本无法支持可靠性判断，“无报告”也可能只是没有暴露或没有诊断。

**答案**：增加独立安装、长会话、压缩和逐 Tool 暴露量，明确分子、分母、失败分类，并把外部数据限定为 Beta 可用性信号。

> [→ 正文 §9 已体现]

#### Q#6：为什么取消固定四周承诺？

> 2026-07-27 | 严格计划审查 | 工期证据

**问题**：原四周计划没有 Owner、估算、依赖和缓冲，单周范围包含多个 Runtime/Data Integrity 子系统。

**答案**：改用人日估算和 Gate 顺序。日历时间在 Issue 完成细分后更新，任何日期不得绕过 Gate。

> [→ 正文 §6 已体现]

#### Q#7：为什么 Beta 不自动安装 Cron？

> 2026-07-27 | 计划实施性补强 | 跨平台与破坏性边界

**问题**：自动修改 crontab、systemd 或 launchd 会引入平台分支、权限、重复注册和卸载恢复风险，而当前 Cron 本身也没有完整 schedule/install 链路。

**答案**：Beta 固定提供手工 `deepseek-harness audit`，Cron 仅作为 Experimental 示例。安装器不得修改用户定时任务，避免把非核心能力变成发布阻断和用户环境副作用。

> [→ 正文 §2.7、OPS-001 已体现]

#### Q#8：为什么 Migration 不能留到 Stable？

> 2026-07-27 | PRD 反向追踪 | Beta 升级契约

**问题**：原顺序把 `MIG-001` 放在 M6，但 PRD 的 `FR-INSTALL-004` 和 §18 已承诺从当前版本升级到 Beta 时执行显式 migration 和失败回滚。

**答案**：`MIG-001` 前移到 M4，并成为 G3 前置条件；Beta 发布前必须用审查基线 DB、Config 和 Markdown fixture 验证迁移、回滚与拒绝降级。M6 只对最终 RC 重跑 Release Gate，不再首次实现迁移。

> [→ 正文 §5 G3、§6.6 已体现]
