# oh-my-deepseek-harness

An Agent plugin system with deep optimizations for DeepSeek. 14 Agent engineering patterns implemented, 4 DeepSeek V4 API-layer physical property optimizations coming soon.

English | [简体中文](README.md)

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-green)](https://python.org)
[![Hermes Agent v0.18+](https://img.shields.io/badge/hermes-%3E%3D0.18.0-purple)](https://github.com/HermesAgent/hermes)
[![Tests](https://img.shields.io/badge/tests-144%20cases-brightgreen)](tests/)

---

## Why This Project Exists

DeepSeek V4 has several unique API-layer and model-layer physical characteristics (reasoning_content structure, DSML tool calling format, Quick Instruction routing, reasoning effort control), but generic Agent frameworks don't optimize for these. Meanwhile, Agent engineering practices (cognitive gating, constraint immunity, intent routing) also lack systematic implementation.

Built on the Hermes Agent Plugin system, this project translates DeepSeek's physical properties into runnable Agent capabilities through a four-layer architecture of plugins, an independent context engine, MCP microservices, and a platform-agnostic core. It does not modify a single line of Hermes core code.

## Implemented Core Features

- ✅ **Cognitive Gate** (I-02 Bidirectional Primitives + I-08 Scope Control): Automatically injects L1 honor/shame values, L2 thinking patterns, and L3 exclusion list into every conversation turn
- ✅ **Constraint Immune System** (I-01 Hard Constraint Detection + Periodic Audit): Detects constraints like "must not / cannot", automatically logs violations, and runs daily cron audits
- ✅ **Intent Router** (I-10 7+1 Classification + Policy Binding): Keyword matching identifies 7+1 user intent types, binding different interview depth, Plan granularity, review standards, and execution modes
- ✅ **Reasoning Strip** (I-14 Provider-Aware Stripping): Strips thinking tokens for DeepSeek/OpenAI (not counted in cache, pure waste), retains them for Anthropic (signed thinking block needs to be echoed back)
- ✅ **Tool Quality Assessment** (post_tool_call content integrity check): Automatically validates results of write/read/bash tool calls, intercepts empty results and exceptions
- ✅ **Session Learning** (I-09 Skill Proposal): Identifies reusable Skill patterns in long conversations and appends them to feedback-lessons.md
- ✅ **Daily Reflection**: Reads state.db via daily cron to count conversation turns and Token consumption, generates reflection reports in reflections/
- ✅ **Subtask Watch**: Tracks subagent_start/subagent_stop events, records each subtask's start, end, and result
- ✅ **Context Compression Engine** (I-03/I-04/I-07/I-13 Independent Context Engine Plugin): Uses DeepSeek API for independent context compression, does not depend on Hermes auxiliary_client
- ✅ **OKR Plan Engine MCP** (I-06 Cascading Correction FastAPI Service): PlanStep DAG orchestration + cascading correction, port 8200
- ✅ **Memory Tagger MCP** (I-12 Lambda Filtering FastAPI Service): Memory tag middle layer + lambda function filtering, port 8100
- ✅ **Checkpoint Review MCP** (I-11 Snapshot Review FastAPI Service): Checkpoint snapshot review state machine, port 8300
- ✅ **Platform-Agnostic Core** (packages/platform_core/): Pure Python module that extracts common plugin logic, usable independently from Hermes

## Architecture (4 Layers)

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Hermes Plugin (plugins/deepseek-harness/)         │
│  9 Python files · 8 Hook registration points · v2.0.0       │
│  pre_llm_call(4) + post_tool_call + on_session_end          │
│  + subagent_start + subagent_stop                           │
├──────────────────────────────────────────────────────────────┤
│  Layer 2: Context Engine Plugin (plugins/deepseek-context/) │
│  Independent LLM client · no Hermes auxiliary_client dep     │
│  I-03/I-04/I-07/I-13 four patterns implemented here         │
├──────────────────────────────────────────────────────────────┤
│  Layer 3: MCP Servers (mcp/)                                │
│  plan-engine:8200 · memory-tagger:8100 · checkpoint:8300    │
│  Three independent FastAPI microservices · SQLite persistence│
│  · MCP protocol communication                               │
├──────────────────────────────────────────────────────────────┤
│  Layer 4: Platform Core (packages/platform_core/)           │
│  Pure Python · no Hermes dependency · pip installable        │
│  gate/adapter/assessor/intent_router/reasoning_strip ...    │
└──────────────────────────────────────────────────────────────┘
```

### Layer 1: Hermes Plugin

`plugins/deepseek-harness/` contains 9 files injected through 8 Hook points:

| File | Hook | Trigger | Function |
|------|------|---------|----------|
| gate.py | pre_llm_call | Before every LLM call | Cognitive reminder + MAP navigation |
| reasoning_strip.py | pre_llm_call | Before every LLM call | Provider-aware thinking token stripping |
| intent_router.py | pre_llm_call | Before every LLM call | 7+1 intent classification + policy binding + exclusion list |
| immune_audit.py | pre_llm_call | Optional on first turn | Constraint violation detection reminder |
| assessor.py | post_tool_call | After every tool call | Content integrity check |
| learner.py | on_session_end | At session end | Skill proposal appended to feedback log |
| subagent_watch.py | subagent_start/stop | On subtask start/stop | Records subtask status and result |

### Layer 2: Context Engine Plugin

`plugins/deepseek-context/` is an independent LLM client plugin that calls the DeepSeek API directly, bypassing the Hermes auxiliary_client mechanism. It handles context compression, summarization, and structural reorganization (I-03 outer compression / I-04 time decay / I-07 inner compression / I-13 structural compression).

### Layer 3: MCP Servers

Three independently running FastAPI microservices that communicate with Hermes through the MCP protocol:

- **plan-engine** (port 8200): OKR PlanStep DAG orchestration engine supporting cascading correction for multi-level Plans (I-06)
- **memory-tagger** (port 8100): Memory content tagging and lambda function filtering (I-12)
- **checkpoint-review** (port 8300): Checkpoint snapshot review state machine supporting multi-round review workflows (I-11)

All services use SQLite for persistence and are automatically started when the plugin loads (auto_start: true).

### Layer 4: Platform Core

`packages/platform_core/` is a pure Python module containing platform-agnostic logic extracted from the main plugin. It includes modules like gate, assessor, intent_router, reasoning_strip, learner, adapter, and sub-packages for checkpoint, memory_tagger, plan_engine, context, etc. It can be pip installed independently with no dependency on any Hermes code.

## Quick Start

```bash
git clone https://github.com/yuanchenglu/oh-my-deepseek-harness.git
cd oh-my-deepseek-harness

# Preview backup plan (no write operations)
bash scripts/install.sh --dry-run

# Execute installation (auto-backups existing memory, no overwrite, no delete)
bash scripts/install.sh

# Verify plugin is registered
hermes plugins list | grep deepseek
```

The install script automatically handles: backup SOUL.md/MEMORY.md/USER.md, create plugin symlinks, register Hooks, and install dependencies.

## Directory Structure

```
oh-my-deepseek-harness/
├── plugins/
│   ├── deepseek-harness/          # Main plugin (9 files, 8 hooks, v2.0.0)
│   │   ├── plugin.yaml            # Plugin declaration + I-01~I-14 mapping
│   │   ├── __init__.py            # Registration entry (7 handlers)
│   │   ├── gate.py                # Cognitive gate (I-02 + I-08)
│   │   ├── reasoning_strip.py     # Reasoning strip (I-14)
│   │   ├── intent_router.py       # Intent router (I-10)
│   │   ├── immune_audit.py        # Constraint audit (I-01)
│   │   ├── assessor.py            # Tool quality assessment
│   │   ├── learner.py             # Session learning (I-09)
│   │   ├── subagent_watch.py      # Subtask watch
│   │   └── strategies.yaml        # 7+1 intent strategy config
│   └── deepseek-context/          # Context engine plugin (independent LLM client)
│       ├── plugin.yaml
│       ├── __init__.py
│       ├── compressor.py          # I-03/I-04/I-07/I-13 compression
│       └── config.yaml
├── mcp/
│   ├── plan-engine/               # OKR PlanStep DAG engine (I-06, port 8200)
│   │   ├── server.py, engine.py, models.py, storage.py
│   ├── memory-tagger/             # Memory lambda filtering (I-12, port 8100)
│   │   ├── server.py, tagger.py, models.py, storage.py, config.yaml
│   └── checkpoint-review/         # Snapshot review state machine (I-11, port 8300)
│       ├── server.py, models.py, storage.py
├── packages/
│   └── platform_core/             # Platform-agnostic core (pure Python, 0 Hermes deps)
│       ├── pyproject.toml
│       ├── gate.py, assessor.py, intent_router.py, ...
│       ├── adapter.py             # Hermes to Platform adapter layer
│       └── checkpoint/, context/, memory_tagger/, plan_engine/
├── scripts/
│   ├── install.sh                 # One-click install + auto backup
│   └── daily-reflection.sh        # Daily reflection (cron)
├── crons/
│   └── immune-audit.cron          # I-01 periodic constraint audit (daily 3:00)
├── tests/                         # pytest unit tests (159 cases, 16 files)
├── docs/research/                 # Research documentation
├── README.md
├── README_EN.md
└── LICENSE                        # MIT
```

## 14 Agent Engineering Patterns + Upcoming DeepSeek V4 Physical Properties

| ID | Pattern Name | Status | Description |
|----|-------------|--------|-------------|
| I-01 | Hard Constraint Detection & Periodic Audit | ✅ | Parses "must not / cannot" instructions, logs violations, daily cron audit report |
| I-02 | Bidirectional Primitives (Affirmative + Negative) | ✅ | Three-layer cognitive architecture: L1 honor/shame values + L2 thinking patterns + L3 exclusion list |
| I-03 | Outer Context Compression | ✅ | Context Engine produces compressed summaries of raw conversation history |
| I-04 | Time-Decay Context Ordering | ✅ | Recent content retains detail, older content is automatically summarized |
| I-05 | Memory Tagging Middle Layer | ✅ | Memory Tagger MCP service (original I-12 ID, later split into standalone MCP) |
| I-06 | Cascading Plan Correction | ✅ | Plan Engine MCP service, auto cascading impact analysis after PlanStep changes |
| I-07 | Inner Context Compression | ✅ | Context Engine performs structural compression at the system prompt level |
| I-08 | Scope Control (Exclusion List) | ✅ | Layer 1 Metis reverse questioning, auto-generates "not doing this time" exclusion list |
| I-09 | Skill Proposal & Auto Learning | ✅ | Detects reusable Skill patterns before long conversations end, appends to feedback log |
| I-10 | 7+1 Intent Classification & Policy Binding | ✅ | refactor/new/medium/collaboration/architecture/research/simple + spec_driven fallback |
| I-11 | Checkpoint Snapshot Review | ✅ | Checkpoint Review MCP service, snapshot comparison + rollback decision |
| I-12 | Memory Lambda Function Filtering | ✅ | Memory Tagger MCP service, lambda expression filtering of irrelevant memories |
| I-13 | Structural Context Compression | ✅ | Context Engine selects compression strategy by data structure (code/config/docs) |
| I-14 | Provider-Aware Reasoning Strip | ✅ | Selectively strips thinking tokens by provider type: stripped for DeepSeek/OpenAI, retained for Anthropic |
| I-15 | DSML Tool Call Optimization | ➖ | Server-side auto-converted; no plugin needed |
| I-16 | Quick Instruction Routing | ➖ | V4 internal mechanism; not available via OpenAI-compatible API (I-10 intent routing is alternative) |
| I-17 | Reasoning Effort Control | ✅ | Dynamically sets reasoning_effort (max/high) based on I-10 intent classification. Spike verified 3x reasoning token increase |
| I-18 | Latest Reminder Injection | ✅ | Fallback: injects current datetime into system prompt on first turn (latest_reminder role not supported by API) |

All 16 patterns (I-01 through I-18 feasible subset) are implemented and shipped in v2.1.0.

## Roadmap

- ✅ **v1.0 Foundation Plugin**: Cognitive gate + quality assessment + learning summary + subtask watch (completed)
- ✅ **v2.0 Four-Layer Architecture**: Plugin + Context Engine + MCP microservices + Platform Core (completed)
- ✅ **All 14 Patterns Implemented**: I-01 through I-14 fully shipped (completed)
- ✅ **v2.1 V4 Feature Validation**: Spike verified I-15~I-18 feasibility + implemented I-17/I-18 (completed)
- 🔲 **Platform Adaptation**: Adapt platform_core to other Agent platforms such as OpenCode and Claude Code
- 🔲 **More Innovation Patterns**: Continue exploring DeepSeek's new API-layer characteristics, extending to I-19 and beyond
- 🔲 **Community Contribution Guide**: Improve CONTRIBUTING.md and developer documentation, lower the barrier to participation

## FAQ

**Does it modify Hermes core code?**
No. It uses only the official Hermes Plugin Hook interfaces (pre_llm_call / post_tool_call / on_session_end / subagent_start / subagent_stop), which have been verified in the source code. Daily Hermes updates will not cause merge conflicts.

**Will it overwrite my existing memory?**
No. SOUL.md, MEMORY.md, and USER.md are automatically backed up as `.bak.{timestamp}` before installation. Original content is not deleted. The install.sh script defaults to --dry-run preview mode, safe with no side effects.

**What environment is required?**
- Hermes Agent >= v0.18.0
- Python >= 3.10
- rsync, sqlite3 CLI, pyyaml (needed for some features, not mandatory)

**Does it conflict with MemOS plugin?**
No. They use different Plugin Hooks and file paths, operating independently.

**How are MCP services started?**
Three MCP services (plan-engine:8200, memory-tagger:8100, checkpoint-review:8300) are automatically launched when the plugin starts. This can also be controlled via auto_start: true in plugin.yaml.

**Can platform_core be used standalone?**
Yes. `packages/platform_core/` is a pure Python module with no Hermes dependency. It can be installed directly via pip install or imported and used.

## Uninstall

```bash
hermes plugins disable deepseek-harness
rm -rf ~/.hermes/plugins/deepseek-harness/
```

Backup files created during installation (`*.bak.*`) are retained and must be cleaned up manually.

## License

MIT (c) 2026 yuanchenglu

---

*oh-my-deepseek-harness is an open source community project with no direct affiliation to DeepSeek or Hermes Agent.*
