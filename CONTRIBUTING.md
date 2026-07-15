# 贡献指南 | Contributing

感谢你考虑为 oh-my-deepseek-harness 贡献代码。这份文档描述了开发环境的配置、编码规范、提交约定、测试要求和分支策略。

## 开发环境设置 | Development Setup

### 前置要求

- Python ≥ 3.10
- Hermes Agent ≥ v0.18.0（运行插件需要）
- git、rsync、sqlite3 CLI（部分功能需要）

### 克隆与安装

```bash
git clone https://github.com/yuanchenglu/oh-my-deepseek-harness.git
cd oh-my-deepseek-harness

python3 -m venv .venv
source .venv/bin/activate

# 安装平台核心模块（开发模式）
pip install -e packages/platform_core/

# 验证测试全部通过
pytest -v
```

平台核心包 `platform-core` 已配置 `pyproject.toml`，支持 `pip install -e .` 开发模式安装。插件目录下的 `.py` 文件由 `conftest.py` 自动添加到 `sys.path`，无需额外安装。

### 了解测试环境

测试文件位于 `tests/` 目录（14 个文件，共 144 个测试用例）。`conftest.py` 自动完成两件事：

1. 对 `agent` 和 `agent.context_engine` 做 mock，让 CI 环境无需安装 Hermes 即可运行单元测试
2. 创建 `plugins/deepseek_harness` → `deepseek-harness` 的符号链接（Python import 不支持连字符）

新增测试文件时，无需额外配置，放在 `tests/` 下即可被 pytest 发现。

## 编码规范 | Code Style

### 类型注解

所有函数必须有完整的类型注解。这是硬性要求——每个参数类型和返回值类型都必须显式声明。

```python
# 正确 ✅
def classify_intent(task_description: str) -> Dict[str, Any]:
    ...

# 错误 ❌
def classify_intent(task_description):
    ...
```

### 文档字符串

使用 Google 风格的 docstring。中文优先，英文术语（如 kwargs、callback）可以保留。

```python
def on_pre_llm_call(**kwargs) -> Optional[Dict[str, Any]]:
    """注入认知提醒、双向原语和范围控制到 user message。

    首轮注入完整 MAP.md + L1/L2 + I-02 完整 + I-08 完整。
    后续轮仅注入 L1/L2 + 简短 I-02 + 简短 I-08。

    Args:
        **kwargs: 包含 is_first_turn, session_id 等上下文。
            session_id: str — 当前会话 ID
            is_first_turn: bool — 是否为首轮调用
            model: str — 当前使用的模型名称

    Returns:
        包含 'context' key 的 dict，注入文本在其中。
        至少返回纯 L1/L2 的 dict，不会返回 None。

    Raises:
        不显式抛异常。所有 IO 操作在 try/except 内静默降级。
    """
```

### 中文注释优先

非显而易见的逻辑必须使用中文注释。项目面向中文社区，中文可读性优于英文。

```python
# ── I-01: 从用户消息中提取硬约束，更新横切状态通道 ──
matches = _HARD_CONSTRAINT_PATTERN.findall(user_message)
if matches:
    _current_hard_constraints.clear()
    _current_hard_constraints.update(c.strip() for c in matches if c.strip())
```

### 风格要点

- 遵循现有文件的风格（参考 `gate.py`、`assessor.py`、`intent_router.py` 等）
- 模块级别用 `"""docstring"""` 说明模块功能和工作模式
- 私有函数加 `_` 前缀（如 `_core_reminders()`）
- 常量用大写 + 下划线（如 `_HARD_CONSTRAINT_PATTERN`）
- 日志使用标准 `logging.getLogger(__name__)`，不要用 `print()`
- 文件级别分隔用 `# ──` 注释块
- 所有 `except` 必须说明静默降级的原因

### 关于 SLOP

AI 辅助生成的代码中，以下模式需要避免：

- 无意义的相等性对比（`a == True` → `a`）
- 过度复杂的单行表达式（拆成多行）
- 超过 250 行的模块（应当拆分子模块或子包）
- 重复的 if/elif 链（考虑用 dict 映射替代）

## 项目结构 | Project Structure

贡献前先了解项目的四层架构：

```
oh-my-deepseek-harness/
├── plugins/deepseek-harness/    # Layer 1: Hermes Plugin (8 hooks)
├── plugins/deepseek-context/    # Layer 2: 独立上下文引擎
├── mcp/                         # Layer 3: MCP 微服务
│   ├── plan-engine/             #   PlanStep DAG 引擎 (8200)
│   ├── memory-tagger/           #   Memory λ 过滤 (8100)
│   └── checkpoint-review/       #   快照审查状态机 (8300)
├── packages/platform_core/      # Layer 4: 平台无关核心
├── scripts/                     # 安装与运维脚本
├── crons/                       # 定时任务
├── tests/                       # 测试 (144 用例, 14 文件)
└── docs/                        # 文档
```

修改 Layer 1 插件时注意 8 个 Hook 的注册顺序。修改 Layer 4 时确保不引入 Hermes 依赖。

## 测试要求 | Testing Requirements

- 每个新功能必须有对应的测试覆盖
- 测试文件命名为 `test_<模块名>.py`，放在 `tests/` 目录下
- 如果新增的模块需要 mock Hermes 依赖，在 `conftest.py` 中添加 mock
- 提交前运行全部测试并确保通过：

```bash
pytest -v          # 运行全部 144 个测试
pytest -v tests/test_gate.py  # 运行单个测试文件
pytest -v -k "keyword"        # 按关键词筛选测试
```

CI 环境不安装 Hermes，因此所有测试必须能在 mock Hermes 依赖后独立运行。

## 提交约定 | Commit Convention

### 格式

双向标题——英文在前，中文在后，中间用 `|` 分隔：

```
<类型>(<范围>): <英文描述> | <简体中文描述>
```

类型使用 Conventional Commits：

| 类型 | 用途 |
|------|------|
| feat | 新功能 |
| fix | 修复 bug |
| docs | 文档变更 |
| chore | 构建、CI、工具链 |
| ci | CI 配置变更 |
| refactor | 重构（不改变外部行为） |
| test | 测试相关 |
| style | 代码格式（不影响逻辑） |

### 示例

```
feat(gate): add environment variable injection in pre_llm_call | gate: pre_llm_call 增加环境变量注入
fix(assessor): handle empty constraint set gracefully | assessor: 处理空约束集合时的边界情况
docs: add CONTRIBUTING.md | 新增贡献指南
refactor(intent_router): replace if-chain with keyword-strategy map | intent_router: 用策略映射表替换 if 链
```

### 原子提交原则

- 一个 commit 只做一件事
- 不要混合同类改动（如 docs 和 feat 放在不同 commit）
- 每个 commit 必须通过全部测试

## 分支策略 | Branch Strategy

| 分支 | 用途 | 说明 |
|------|------|------|
| `master` | 发布分支 | 受保护，必须通过 PR 合并 |
| `feat/<name>` | 功能开发 | 从 master 创建 |
| `fix/<name>` | 缺陷修复 | 从 master 创建 |
| `docs/<name>` | 文档更新 | 从 master 创建 |

### 工作流

1. 从 `master` 创建功能分支：`git checkout -b feat/my-feature`
2. 在分支上开发和测试
3. 确保全部测试通过：`pytest -v`
4. 提交代码（遵循提交约定）
5. 推送到 GitHub：`git push origin feat/my-feature`
6. 创建 Pull Request 到 `master`
7. 等待 Review 和 CI 通过后合并

## Pull Request 规范

- PR 标题遵循提交格式（`<类型>: <描述>`）
- PR 描述说明改动背景、技术方案和验证方式
- 如果改动涉及多个模块，列出每个模块的变更要点
- 包含测试通过的截图或日志（非必需但推荐）

## 问题与讨论 | Issues

- Bug 报告：描述复现步骤、期望行为和实际行为，附上日志或截图
- 功能请求：说明背景、使用场景和价值
- 架构讨论：欢迎在 Issue 中讨论新的设计模式（I-15 及以后）

---

再次感谢你的贡献。对于任何问题，请直接提交 Issue。
