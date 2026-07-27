# 贡献指南 | Contributing

感谢你考虑为 `oh-my-deepseek-harness` 贡献代码。本仓库处于 Open-source Beta 稳定化周期，当前唯一目标是完成可安装性、数据完整性、安全边界、测试和发布闭环。

> 当前状态：Plan Ready 已通过；M0 正在执行；G0 尚未通过。贡献不得绕过 `docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md` 与规范性 Errata。

## 1. 开始前必读 | Required Reading

按顺序阅读：

1. `docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md`
2. `docs/roadmap/OPEN_SOURCE_RELEASE_PLAN_ERRATA_2.3.md`
3. 目标 GitHub Issue 中的 Work ID、依赖、允许文件和验收条件
4. `docs/architecture/TECHNICAL_ARCHITECTURE.md`
5. `docs/product/PRD.md`
6. `docs/testing/TEST_PLAN.md`

一次只实施一个 Work ID。没有 Work ID、Issue 或明确验收测试的改动，不进入当前发布周期。

## 2. 开发环境 | Development Environment

### 支持范围

- Python 3.10、3.11、3.12；
- Linux、macOS；
- Hermes 正式兼容版本由 `COMPAT-000` 固定；在此之前不得自行扩大兼容承诺；
- Git。

Python package metadata 固定为 `>=3.10,<3.13`。Windows/WSL 可用于实验，但不是当前 Beta 支持承诺。

### 当前基线安装

当前仓库仍处于 package/runtime 重构前阶段。普通贡献者可使用现有开发依赖运行基线测试：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,mcp]"
pytest -ra
```

最终发布安装契约是：

```bash
python -m pip install "oh-my-deepseek-harness[all]==3.0.0b1"
deepseek-harness install
deepseek-harness doctor
```

该最终契约将在 M1 实现。当前 editable install 只能作为开发基线，不构成 Release Evidence。

## 3. 测试隔离 | Test Isolation

所有测试必须使用临时 HOME、数据根、数据库和动态端口：

```bash
test_home=$(mktemp -d)
mkdir -p "$test_home/home" "$test_home/data"
test_port=$(python -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')

env \
  HOME="$test_home/home" \
  HARNESS_CONFIG_PATH="$test_home/data/config/config.yaml" \
  HARNESS_DATA_ROOT="$test_home/data" \
  HARNESS_DB_PATH="$test_home/data/harness.db" \
  HARNESS_HOST="127.0.0.1" \
  HARNESS_PORT="$test_port" \
  DEEPSEEK_API_KEY=fake \
  pytest -ra
```

禁止：

- 读取或修改真实 `~/.hermes`；
- 使用真实用户 DB、Memory、Prompt 或 Secret；
- 普通 CI 访问外部 API；
- 依赖开发机已有 package、源码 symlink 或仓库相对路径证明发布可用；
- 用重试、skip 或弱化断言掩盖缺陷。

在 `QA-001` 建立正式通道前，至少运行目标测试和完整 `pytest -ra`。之后统一使用 `make test-fast`、`make test-integration`，Release 类 Work ID 还必须运行 `make test-release`。

## 4. 分支策略 | Branch Strategy

完整政策见 `docs/contributing/BRANCH_POLICY.md`。

| 分支 | 用途 | 规则 |
|---|---|---|
| `develop` | 唯一开发集成分支与目标默认分支 | 普通 PR 的唯一目标；不得直接推送业务变更 |
| `master` | Release Gate 通过后的可发布基线 | 只接收 G3 通过后的 `develop → master` RC PR |
| `fix/<scope>` | P0/P1 修复 | 从 `develop` 创建，PR 回 `develop` |
| `test/<scope>` | 测试基础设施或回归规格 | 从 `develop` 创建，PR 回 `develop` |
| `docs/<scope>` | 文档和治理 | 从 `develop` 创建，PR 回 `develop` |
| `chore/<scope>` | 构建、版本、CI、工具链 | 从 `develop` 创建，PR 回 `develop` |
| `feat/<scope>` | 经计划明确批准的必要功能 | 必须有 Work ID；默认不接受新增功能 |

标准流程：

```bash
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch -c fix/<work-id>-<scope>
```

完成后向 `develop` 创建 PR。普通贡献不得向 `master` 创建业务 PR。Release PR 由 Gate 协调者在 G3 PASS 后发起。

## 5. Work ID 与变更边界 | Work Scope

每个执行 Issue 必须包含：

- Work ID、Requirement ID、CR/XF ID 和优先级；
- 当前行为、期望行为和最小复现；
- 可证伪假设及其源码/测试依据；
- Owner、估算和硬依赖；
- 允许修改的路径；
- 自动验收测试和失败输出；
- 配置、数据、隐私和兼容性影响；
- Upgrade/Rollback；
- 文档改动和明确不做事项。

若实现必须修改 Issue 未授权路径，停止并更新计划/Issue；不得临场扩大范围。一个 Commit 只对应一个 Work ID。

## 6. 编码规范 | Coding Standards

### 类型与边界

- 所有公共函数和领域服务必须有类型注解；
- Hermes Adapter、FastAPI Adapter 与领域逻辑分离；
- Tool、API 和 Storage 的输入模型必须来自单一契约源；
- 运行时状态必须按 Session 或明确生命周期隔离；
- 数据写入必须使用事务和明确不变量；
- 辅助能力失败必须可诊断并按契约降级。

### 日志与错误

- 使用 `logging.getLogger(__name__)`，不得用 `print()` 代替运行日志；
- 错误必须包含稳定 error code 和用户可执行的恢复建议；
- 默认不记录 Prompt、Tool Result、Memory 原文、Secret 或绝对敏感路径；
- 禁止把原始异常 traceback 返回给模型或普通用户。

### 变更纪律

- 最小实现，不顺手重构；
- 不批量格式化无关文件；
- 不新增 Innovation 或非目标平台；
- 不复制第二份业务实现绕过 package/compatibility 问题；
- 不把降级实现描述为原生模型或 Hermes 能力。

## 7. 当前与目标仓库结构 | Repository Layout

当前审查基线仍主要使用：

```text
plugins/deepseek-harness/
plugins/deepseek-context/
mcp/harness_server/
packages/platform_core/
tests/
docs/
```

M1 目标结构是：

```text
src/
├── deepseek_harness/
├── deepseek_context/
└── harness_server/
```

在 `PKG-001` 完成前，不得假装目标结构已经存在；完成后旧目录只允许保留 Hermes 所需的 manifest 和薄适配入口，不得保留第二套业务源码。

## 8. 测试要求 | Testing Requirements

每个 Work ID 必须同时提供：

1. 文件层证据：文件可解析、构建或安装；
2. 集成层证据：真实调用方 import 并调用实现；
3. 管线层证据：用户入口到可观察结果完整通过。

已知缺陷使用 strict XFAIL 固化。修复后必须删除 XFAIL 并保持断言强度。不得把 XPASS 当作成功后继续保留标记。

提交前至少运行：

```bash
pytest -ra
git diff --check
```

若 CI 失败，读取日志并修复根因；不得仅重跑失败任务掩盖稳定缺陷。

## 9. Commit 约定 | Commit Convention

Commit 使用双语格式：

```text
<type>(<scope>): English title | 简体中文标题

English:
<what changed, why, and verification>

简体中文:
<改了什么、为什么、如何验证>
```

类型：`feat`、`fix`、`docs`、`chore`、`ci`、`refactor`、`test`、`style`。

标题示例：

```text
fix(ctx-001): preserve tail message uniqueness | 保证尾部消息唯一性
```

## 10. Pull Request 要求 | Pull Requests

PR 必须使用仓库模板，并包含：

- Work ID 与 Issue；
- Requirement/Test/CR/XF 链接；
- 当前行为、期望行为和实现假设；
- 修改文件及范围说明；
- 测试命令和 Passed/Failed/XPASS/XFAIL 数量；
- 数据、隐私、安全、兼容和迁移影响；
- Rollback；
- Evidence 文档和 CI Run；
- 明确不做事项。

合并条件：

- 硬依赖已完成；
- Required CI 全绿；
- 无越界文件；
- 正常、边界和故障测试通过；
- 文档与实际能力一致；
- Requirement → Test → PR → Commit → Evidence 可追踪。

默认使用 Squash Merge，使一个 Work ID 在 `develop` 上形成一个可回滚 Commit。

## 11. 安全停止条件 | Stop Conditions

出现以下任一情况必须停止并在 Issue 中报告：

- 需要真实 Token、PyPI/GitHub 发布权限或用户账号；
- 需要删除/迁移用户数据但没有备份与 rollback 测试；
- Hermes 实际接口与固定兼容版本不一致；
- 新依赖改变许可证、安全或支持平台；
- 发现新的 P0 或现有通过测试非预期回归；
- Requirement、Schema 和现有数据无法同时兼容；
- 需要修改未授权业务域。

## 12. 当前发布限制 | Release Restrictions

在 G0 通过前不得开始 M1。在 G3 通过前不得向 `master` 合入 Release Candidate。在 G5 通过前不得发布 `v3.0.0`。

任何贡献都不得创建、移动或覆盖 Git Tag，不得上传 PyPI，不得替换 GitHub Release 制品，除非对应 Release Work ID 已明确授权。
