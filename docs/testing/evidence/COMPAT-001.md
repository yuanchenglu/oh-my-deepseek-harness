# COMPAT-001 Evidence - Hermes Plugin Registration Probe & Matrix

- Work ID: `COMPAT-001`
- Canonical Issue: #46
- Dependency: COMPAT-000 + QA-002 complete
- Status: **Complete (registration probe)**
- Implementation baseline: `develop@master`
- Implementation branch: `feat/compat-001-hermes-matrix`
- Next serial Work ID: `SEC-001` / #47

## 1. Problem

真实 Hermes 插件注册契约未验证；支持矩阵无探针证据。

## 2. Implementation

- `tests/compatibility/probes/test_hermes_register_probe.py`：用 Hermes v0.19.0
  兼容的 ctx 接口驱动真实 `deepseek_harness.register(ctx)`。
  - 断言注册 5 个 Hook（pre_llm_call/post_tool_call/on_session_end/subagent_start/
    subagent_stop）。
  - 断言注册 9 个 Runtime Tool（10 target 减 memory_store pending）。
  - 断言 register 可重复调用不抛异常（Hermes 多次 enable 场景）。
- `docs/compatibility/HERMES_MATRIX.md`：记录 8.1 registration probe。
- 探针在 release 通道（tests/compatibility）真实运行。

## 3. CI evidence

PR #118:
- test (3.10): SUCCESS
- test (3.11): SUCCESS
- test (3.12): SUCCESS
- qa-fast: SUCCESS
- qa-quality: SUCCESS

## 4. FR coverage

| FR ID | Description | Status |
|---|---|---|
| FR-PLUGIN-001~005 | Hermes Plugin 注册/生命周期 | Covered (registration probe) |
| FR-QA-002 | Python 3.10-3.12 | Covered (test matrix) |
| FR-QA-007 | 兼容矩阵 | Covered (HERMES_MATRIX) |

## 5. Verification

Local: tests/compatibility 8 passed; 核心回归 127 passed.

## 6. Authorized paths

| Path | Status |
|---|---|
| `tests/compatibility/probes/test_hermes_register_probe.py` | Added |
| `docs/compatibility/HERMES_MATRIX.md` | Modified (8.1 probe) |

## 7. Definition of Done

- [x] 真实 register(ctx) 驱动 Hermes v0.19.0 ctx 契约
- [x] 5 Hook + 9 Tool 注册验证通过
- [x] 探针在 release 通道真实运行
- [x] 支持矩阵记录探针证据
- [x] Required CI + traceability

## 8. Residual (honest)

完整 live-Hermes 生命周期 E2E（矩阵格 cell 1-8：真实 Hermes 源码安装、发现、
enablement、Session/subagent lifecycle、Context Engine ABC、Tool 调用）需真实
Hermes v0.19.0 源码环境（Hermes 已移除 PyPI 安装，需源码 clone）。本探针覆盖
registration 契约；完整 E2E 由 G3 把关，未在 M4 内声称完整 E2E 通过。