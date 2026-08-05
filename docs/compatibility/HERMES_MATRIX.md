# Hermes Compatibility Target and Matrix

- Work ID: `COMPAT-000`
- Issue: #17
- Decision date: 2026-07-28
- Last synchronized: 2026-07-29
- Selected candidate: **Hermes Agent v0.19.0**
- Git tag: **`v2026.7.20`**
- Upstream repository: `NousResearch/hermes-agent`
- Candidate status: formal signed release; static contract selected
- Real E2E owner: **`COMPAT-001` #46 / M4 / G3**

## 1. Decision

The Open-source Beta validation target is Hermes Agent v0.19.0 from tag `v2026.7.20`.

COMPAT-000 freezes the candidate identity and executable static probes. It does **not** claim the current project has passed real Hermes discovery, enablement, Hook, Context Engine or Tool E2E. That responsibility remains `COMPAT-001`.

## 2. Python support distinction

Hermes v0.19.0 declares:

```text
requires-python = ">=3.11,<3.14"
```

The project distribution currently declares and tests:

```text
requires-python = ">=3.10,<3.13"
CI = Python 3.10, 3.11, 3.12
```

| Layer | Python | Meaning |
|---|---|---|
| Package/core CI | 3.10、3.11、3.12 | Metadata、pure modules、contracts、regressions、artifact lifecycle |
| Full Hermes-integrated Beta support candidate | 3.11、3.12 | Plugin、Context Engine、Tool real E2E matrix |
| Python 3.10 + Hermes v0.19.0 | Unsupported | Doctor/install must reject clearly; no fabricated E2E pass |
| Python 3.13 | Out of current project range | Hermes permits it, but this Beta cycle does not claim it |

Public documentation must say **Python 3.11–3.12 for full Hermes integration**. Python 3.10 may remain package/core/artifact CI but is not a supported Hermes host.

## 3. Candidate provenance

| Field | Value |
|---|---|
| Upstream project | `hermes-agent` |
| Version | `0.19.0` |
| Tag | `v2026.7.20` |
| License | MIT |
| Python | `>=3.11,<3.14` |
| COMPAT-001 source | exact upstream tag or release artifact resolved from `v2026.7.20` |
| Mutable branch accepted as evidence | No |

`COMPAT-001` must record the exact resolved commit SHA and artifact hash before E2E. A later upstream release does not silently replace this candidate.

## 4. General Plugin contract

The selected release documents a `register(ctx)` entry point and:

- `ctx.register_tool(...)`;
- `ctx.register_hook(...)`;
- `ctx.register_context_engine(...)`;
- user/project plugin-directory discovery;
- pip discovery through `hermes_agent.plugins`;
- explicit third-party enablement through `plugins.enabled`.

The installer and real E2E must prove:

1. deployment through a supported discovery mechanism;
2. explicit enablement where required;
3. no source-tree-only import or development symlink;
4. registration through the real Hermes Plugin manager.

## 5. Hook contract

The v0.19.0 formal Hook list includes:

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

The current product manifest uses a subset:

```text
pre_llm_call
post_tool_call
on_session_end
subagent_start
subagent_stop
```

Static subset validation is complete. `COMPAT-001` must verify real registration, lifecycle payloads, optional/missing fields and failure isolation.

## 6. ContextEngine contract

Hermes v0.19.0 requires:

- property `name`;
- `update_from_response(usage)`;
- `should_compress(prompt_tokens=None)`;
- `compress(messages, current_tokens=None, focus_topic=None)`;
- required token counters, threshold, context length and compression count.

Optional lifecycle/tool methods include:

- `on_session_start`;
- `on_session_end`;
- `on_session_reset`;
- `update_model`;
- `get_tool_schemas`;
- `handle_tool_call`;
- `should_compress_preflight`;
- `get_status`.

Only one Context Engine can be active, and activation is explicit through `context.engine`. Presence of installed files is not proof of activation.

Static source inspection found the required property, methods and counters in `DeepSeekContextEngine`. This remains source-level evidence only.

## 7. Static COMPAT-000 probes

Committed probes verify:

- exact candidate version/tag/Python range;
- current Hook names are a subset of the selected Hook list;
- target Tool count remains 10 and Runtime remains 9 until `CON-001 + MEM-001`;
- required ContextEngine ABC names/counters/property are present;
- active support documents distinguish package/core Python from full Hermes-integrated Python.

Static probes do not replace installation or real lifecycle tests.

## 8. COMPAT-001 real E2E plan

| OS | Python | Hermes | Expected |
|---|---|---|---|
| Linux | 3.11 | v0.19.0 / `v2026.7.20` | Full E2E pass |
| Linux | 3.12 | v0.19.0 / `v2026.7.20` | Full E2E pass |
| macOS | 3.11 | v0.19.0 / `v2026.7.20` | Full E2E pass |
| macOS | 3.12 | v0.19.0 / `v2026.7.20` | Full E2E pass |
| Linux/macOS | 3.10 | v0.19.0 | Expected precondition rejection |

Each supported cell must verify:

1. clean Hermes installation from the fixed release source;
2. Plugin discovery and explicit enablement;
3. `register(ctx)` and Hook registration;
4. Session/subagent lifecycle payload handling;
5. Context Engine discovery, registration, explicit selection and ABC calls;
6. current/target Tool registration contract and implemented Tool calls;
7. no real HOME, user DB, prompts or secrets in fixtures;
8. exact OS/Python/Hermes/project SHA/artifact/JUnit evidence.

### 8.1 COMPAT-001 registration probe (committed)

`tests/compatibility/probes/test_hermes_register_probe.py` drives the real
`deepseek_harness.register(ctx)` against a Hermes v0.19.0-compatible `ctx`
surface and asserts the plugin registers the documented 5 Hooks and all 9
runtime Tools (10 target minus `memory_store`). This proves the plugin is
compatible with the Hermes plugin contract and is importable by the Hermes
Plugin manager. It is a **registration-contract probe**; a full live-Hermes
lifecycle E2E (cell 1-8) remains the residual COMPAT-001 responsibility and
is gated by G3.

## 9. Stop conditions

Stop and reopen the compatibility decision if:

- tag/release provenance cannot be resolved;
- actual v0.19.0 code contradicts the documented interface;
- a required Hook/Context/Tool interface is absent;
- activation requires unsupported Hermes-core modification;
- a supported matrix cell cannot install cleanly;
- public docs claim full Python 3.10 Hermes support.

## 10. Gate ownership clarification

Real Hermes E2E is **not a G1 criterion**.

`COMPAT-001` depends on `QA-002` and is located in M4. Treating it as a G1 requirement would create the impossible cycle:

```text
G1 → M2 → G2 → M3 → M4/QA-002 → COMPAT-001 → G1
```

Therefore:

- G1 covers package/artifact/Runtime/install lifecycle and isolation;
- G2 covers Context/Session/Privacy integrity;
- G3 requires the real Hermes matrix from `COMPAT-001`.

The previous sentence stating that both G1 and G3 required COMPAT-001 evidence was stale and is superseded by this dependency-consistent clarification.
