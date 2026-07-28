# COMPAT-000 Evidence：Hermes 验证目标选择

- Work ID：`COMPAT-000`
- Issue：#17
- Pull Request：#60
- 分支：`docs/compat-000-hermes-target`
- 状态：In Review；待 Required CI 与合并
- 执行日期：2026-07-28

## 1. 结论

唯一 Open-source Beta Hermes 候选固定为：

```text
repository: NousResearch/hermes-agent
version: 0.19.0
tag: v2026.7.20
license: MIT
upstream requires-python: >=3.11,<3.14
```

这是 2026-07-28 核对到的最新正式签名 Release。COMPAT-000 冻结候选、接口和执行计划；不声明真实兼容性已通过。

## 2. Python 版本调查

核对正式版本 metadata：

| Hermes | Tag | requires-python |
|---|---|---|
| 0.13.0 | `v2026.5.7` | `>=3.11,<3.14` |
| 0.14.0 | `v2026.5.16` | `>=3.11,<3.14` |
| 0.15.1 | `v2026.5.29.2` | `>=3.11,<3.14` |
| 0.16.0 | `v2026.6.5` | `>=3.11,<3.14` |
| 0.17.0 | `v2026.6.19` | `>=3.11,<3.14` |
| 0.18.0 | `v2026.7.1` | `>=3.11,<3.14` |
| 0.18.2 | `v2026.7.7.2` | `>=3.11,<3.14` |
| 0.19.0 | `v2026.7.20` | `>=3.11,<3.14` |

“选择近期旧版即可保留完整 Python 3.10 Hermes 支持”的假设被否证。

## 3. 支持分层决策

```text
Package/core CI: Python 3.10, 3.11, 3.12
Full Hermes-integrated Beta: Python 3.11, 3.12
Python 3.10 + Hermes v0.19.0: unsupported precondition
Project Python 3.13: not claimed
OS: Linux, macOS
```

`pyproject.toml` 和当前三版本 CI 不变。Python 3.10 继续验证 package、纯模块和契约回归，但不得被宣传为 Hermes v0.19.0 E2E。后续 `INS-002` Doctor 必须识别并报告不兼容组合。

## 4. Plugin/Hook 静态接口

Hermes v0.19.0 正式文档确认：

- `register(ctx)` Plugin 入口；
- `ctx.register_tool(...)`；
- `ctx.register_hook(...)`；
- `ctx.register_context_engine(...)`；
- user/project Plugin directory discovery；
- pip entry-point group `hermes_agent.plugins`；
- 第三方 general Plugin 需要显式加入 `plugins.enabled`。

正式 Hook 表包括：

```text
pre_tool_call
post_tool_call
pre_llm_call
post_llm_call
on_session_start
on_session_end
on_session_finalize
on_session_reset
subagent_start
subagent_stop
pre_gateway_dispatch
```

当前 Manifest Hook 是上述集合的子集。早期只阅读 Plugins 概览表时曾误以为 `subagent_start` 缺失；完整 Hook 文档确认该 Hook 存在，误判已纠正且未形成代码变更。

## 5. ContextEngine 静态接口

Hermes v0.19.0 ABC 要求：

```text
property: name
methods: update_from_response, should_compress, compress
attributes: last_prompt_tokens, last_completion_tokens, last_total_tokens,
            threshold_tokens, context_length, compression_count
```

当前 `DeepSeekContextEngine` 静态结果：

```text
required property `name`: present as @property; value = deepseek-context
required methods: present
required counters: present
```

PR #60 的第一次探针曾错误地把 `name` 记为缺失。失败的三版本 CI 证明该假设与源码不一致；随后 fixture、probe、矩阵与本 Evidence 已全部改为正向验证。没有为不存在的缺口修改生产代码，也没有把错误责任转移到 `PKG-001`。

静态符合不等于真实兼容。`COMPAT-001` #46 仍需在 Hermes v0.19.0 中完成 discovery、instantiation、explicit selection、ABC 调用和生命周期 E2E。

## 6. 机器可读资产

新增：

- `docs/compatibility/HERMES_MATRIX.md`
- `tests/fixtures/hermes/v0.19.0-contract.yaml`
- `tests/compatibility/probes/test_hermes_target_contract.py`

静态 probes 验证：

- candidate identity 和 Python 分层；
- Project Hook ⊆ official Hook；
- 10 target / 9 current Tool 契约未回退；
- ContextEngine 必需 property/methods/counters 全部存在；
- `name` 必须由真实 `@property` 提供；
- 主计划与双语 README 使用相同支持口径；
- Plugin 与 Context Engine 激活均为显式配置契约。

## 7. COMPAT-001 E2E 矩阵

支持单元：

```text
Linux × Python 3.11 × Hermes v0.19.0
Linux × Python 3.12 × Hermes v0.19.0
macOS × Python 3.11 × Hermes v0.19.0
macOS × Python 3.12 × Hermes v0.19.0
```

负向单元：

```text
Linux/macOS × Python 3.10 × Hermes v0.19.0 → expected rejection/diagnostic
```

每个支持单元必须从固定 Release source 完成 clean install、Plugin discovery/enablement、Hook lifecycle、Context Engine discovery/selection/ABC 和全部实现 Tool E2E，并保存确切 commit/artifact/JUnit。

## 8. 文件范围

修改/新增仅用于候选、契约、静态 probes 和公开支持口径：

- `docs/compatibility/HERMES_MATRIX.md`
- `tests/fixtures/hermes/v0.19.0-contract.yaml`
- `tests/compatibility/probes/test_hermes_target_contract.py`
- `README.md`
- `README_EN.md`
- `docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md`
- `docs/testing/evidence/COMPAT-000.md`

未修改：

- Hermes upstream；
- package metadata；
- CI Python matrix；
- Plugin/Context/Tool 实现；
- installer/Doctor；
- repository settings；
- user data、Secret、Tag 或 Release。

## 9. Gate 判定

COMPAT-000 的完成条件是候选、静态契约和 E2E 计划冻结，不是 E2E 成功。

完成后：

- G0 的“外部候选明确、验证计划可执行”条件可满足；
- G1/G3 的真实兼容性仍由 `COMPAT-001` 阻断；
- 如果静态 probe 或 active support wording 不一致，则 COMPAT-000 不得关闭；
- G0 仍需独立 Gate Evidence。

## 10. Merge-time completion fields

```text
PR: #60
Squash commit:
CI run:
Python 3.10:
Python 3.11:
Python 3.12:
```
