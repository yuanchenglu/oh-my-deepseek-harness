# PRIV-001 Evidence - Outbound and Log Privacy Boundaries

- Work ID: `PRIV-001`
- Canonical Issue: #31
- Dependency: CTX-003 + SES-001 complete
- Status: **Complete**
- Implementation baseline: `develop@d7fd12f`
- Implementation branch: `feat/priv-001-secret-redaction`
- Implementation PR: #95
- Next serial step: **G2 Gate evaluation**

## 1. Problem

No secret redaction before outbound Summary payload. Summary not default-off. No data-sending notice. Config lacked privacy env vars.

## 2. Implementation

### 2.1 Redaction module (`src/deepseek_context/redaction.py`)

6 pattern-based redaction layers:
- OpenAI-style API keys (`sk-` + 20+ alnum)
- Bearer tokens (JWT and long tokens)
- PEM private key blocks (RSA/EC/OPENSSH)
- `.env` style secrets (`KEY=VALUE` where KEY matches secret-like names)
- AWS Access Key IDs (`AKIA...`)
- Generic `key=value` high-entropy secrets

### 2.2 Compressor integration

`serialize_for_summary()` and `generate_summary()` now call `redact_outbound_payload()` before any data leaves the local process. Double redaction (once in serialize, once in generate_summary) as defense-in-depth.

### 2.3 Config defaults (`src/harness_server/config.py`)

New env vars, all default off/false:
- `HARNESS_SUMMARY_ENABLED` (default: false)
- `HARNESS_SUMMARY_ALLOW_TOOL_ARGUMENTS` (default: false)
- `HARNESS_LOG_INCLUDE_CONTENT` (default: false)
- `HARNESS_SUMMARY_OUTBOUND_POLICY` (reserved)

## 3. CI evidence

PR #95:
- test (3.10): COMPLETED/SUCCESS
- test (3.11): COMPLETED/SUCCESS
- test (3.12): COMPLETED/SUCCESS

## 4. TC coverage

| TC ID | Description | Tests | Status |
|---|---|---|---|
| TC-CTX-010 | Secret in Tool Result → outbound and log redaction | `TestToolResultRedaction` (2 tests) | PASS |
| TC-SEC-001 | Secret redaction → outbound and log contain no secrets | `TestSecretRedaction` (6 tests), `TestPrivacyLogs` (1 test) | PASS |

## 5. FR coverage

| FR ID | Description | Status |
|---|---|---|
| FR-CONTEXT-006 | Secret Redaction before outbound | PASS |
| FR-CONTEXT-012 | Data-sending notice with provider/content/disable/redaction | PASS |
| FR-OBS-002 | Privacy logs (no raw prompts, API keys, tool results) | PASS |
| FR-SEC-001 | Outbound Consent (Summary default off) | PASS |
| FR-SEC-002 | Data Minimization (truncated tool args, minimal payload) | PASS |

## 6. Authorized paths

| Path | Status |
|---|---|
| `src/deepseek_context/redaction.py` | New — created |
| `src/deepseek_context/compressor.py` | Modified — redaction hooks |
| `src/harness_server/config.py` | Modified — privacy env vars |
| `tests/test_context_privacy.py` | New — 16 test cases |
| `tests/test_server_process.py` | Modified — env contract update |
