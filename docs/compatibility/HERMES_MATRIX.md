# Hermes Compatibility Target and Matrix

- Work ID: `COMPAT-000`
- Issue: #17
- Decision date: 2026-07-28
- Selected candidate: **Hermes Agent v0.19.0**
- Git tag: **`v2026.7.20`**
- Upstream repository: `NousResearch/hermes-agent`
- Candidate status: formal signed release; static contract selected, real E2E remains `COMPAT-001`

## 1. Decision

The Open-source Beta validation target is Hermes Agent v0.19.0 from tag `v2026.7.20`.

This is the newest formal release observed during COMPAT-000 and contains the current general Plugin system, Hook contracts, `PluginContext.register_tool`, `PluginContext.register_context_engine`, pip entry-point discovery and ContextEngine ABC documentation.

COMPAT-000 freezes the target and executable probes. It does **not** claim the current project has passed real Hermes E2E; that responsibility remains `COMPAT-001`.

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

These are different layers and must not be conflated:

| Layer | Python | Meaning |
|---|---|---|
| Package/core CI | 3.10, 3.11, 3.12 | Package metadata, pure modules, contracts and regressions remain testable |
| Full Hermes-integrated Beta support | 3.11, 3.12 | Supported product matrix for Plugin, Context Engine and Tool E2E |
| Python 3.10 + Hermes v0.19.0 | Unsupported | Hermes cannot be installed under its declared metadata; Doctor/install must report the incompatibility rather than fabricate an E2E pass |
| Python 3.13 | Out of current project range | Hermes allows it, but this project does not claim or test it in the Beta cycle |

Public documentation must say **Python 3.11–3.12 for full Hermes integration**. Python 3.10 may remain in package/core CI but is not a supported Hermes host.

## 3. Candidate provenance

| Field | Value |
|---|---|
| Upstream project | `hermes-agent` |
| Version | `0.19.0` |
| Tag | `v2026.7.20` |
| License | MIT |
| Python | `>=3.11,<3.14` |
| Installation source for COMPAT-001 | exact upstream tag or release artifact resolved from `v2026.7.20` |
| Mutable branch allowed as evidence | No |

`COMPAT-001` must record the exact resolved commit SHA and artifact hash before running E2E. A later upstream release does not silently replace this candidate.

## 4. General Plugin contract

The selected Hermes release documents a `register(ctx)` entry point and the following integration capabilities:

- `ctx.register_tool(...)`;
- `ctx.register_hook(...)`;
- `ctx.register_context_engine(...)`;
- directory discovery from user/project plugin directories;
- pip discovery through the `hermes_agent.plugins` entry-point group;
- explicit enablement of third-party general plugins through `plugins.enabled`.

The installer design must therefore:

1. deploy or expose the Plugin through a supported discovery mechanism;
2. add `deepseek-harness` to the enabled Plugin configuration when required;
3. avoid source-tree-only imports and development symlinks in release evidence;
4. verify registration through the real Hermes Plugin manager.

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

The current project manifest uses a subset:

```text
pre_llm_call
post_tool_call
on_session_end
subagent_start
subagent_stop
```

Static subset validation is part of COMPAT-000. `COMPAT-001` must verify real registration and lifecycle payloads, including missing/optional fields and failure isolation.

## 6. ContextEngine contract

Hermes v0.19.0 requires a ContextEngine implementation to provide:

- property `name`;
- `update_from_response(usage)`;
- `should_compress(prompt_tokens=None)`;
- `compress(messages, current_tokens=None, focus_topic=None)`;
- class attributes/counters for prompt, completion, total tokens, threshold, context length and compression count.

Optional lifecycle and tool methods include:

- `on_session_start`;
- `on_session_end`;
- `on_session_reset`;
- `update_model`;
- `get_tool_schemas`;
- `handle_tool_call`;
- `should_compress_preflight`;
- `get_status`.

Only one Context Engine can be active, and activation is explicit through `context.engine`. The product installer/docs must not claim the engine auto-activates merely because files are present.

## 7. Static COMPAT-000 probes

The committed probe suite verifies:

- fixture version/tag/Python range;
- current Plugin hook names are a subset of the selected Hook list;
- current target Tool count remains 10 and runtime count remains 9 until `CON-001 + MEM-001`;
- `DeepSeekContextEngine` source contains the required v0.19.0 ABC methods/property;
- active support documents distinguish package/core Python from full Hermes-integrated Python.

Static probes do not replace installation or real lifecycle tests.

## 8. COMPAT-001 real E2E plan

Required matrix:

| OS | Python | Hermes | Expected |
|---|---|---|---|
| Linux | 3.11 | v0.19.0 / `v2026.7.20` | Full E2E pass |
| Linux | 3.12 | v0.19.0 / `v2026.7.20` | Full E2E pass |
| macOS | 3.11 | v0.19.0 / `v2026.7.20` | Full E2E pass |
| macOS | 3.12 | v0.19.0 / `v2026.7.20` | Full E2E pass |
| Linux/macOS | 3.10 | v0.19.0 | Expected precondition rejection; not a supported full-product cell |

For each supported cell, COMPAT-001 must verify:

1. clean Hermes installation from the fixed release source;
2. Plugin discovery and explicit enablement;
3. `register(ctx)` and Hook registration;
4. Session start/end and subagent lifecycle payload handling;
5. Context Engine discovery/registration, explicit selection and ABC calls;
6. current/target Tool registration contract and all implemented Tool calls;
7. no real HOME, user DB, prompts or secrets in fixtures;
8. exact environment, commit/artifact and JUnit evidence.

## 9. Stop conditions

Stop and reopen the compatibility decision if:

- the tag or release provenance cannot be resolved;
- actual v0.19.0 code contradicts the documented interface;
- a required Hook/Context/Tool interface is absent;
- Plugin activation requires an unsupported modification to Hermes core;
- a supported cell cannot install from a clean environment;
- product documentation continues to claim full Python 3.10 Hermes support.

## 10. Scope impact

This decision narrows only the **full integrated product support** to Python 3.11–3.12. It does not remove Python 3.10 package/core CI, change `pyproject.toml`, implement adapters, or claim COMPAT-001 has passed.

G0 may proceed after active specifications and static probes are synchronized. G1/G3 still require the real compatibility evidence assigned to `COMPAT-001`.
