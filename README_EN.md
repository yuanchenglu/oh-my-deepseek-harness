# oh-my-deepseek-harness

An Agent plugin system with deep optimizations for DeepSeek. 15 Agent engineering patterns implemented.

English | [简体中文](README.md)

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-green)](https://python.org)
[![Hermes Agent v0.18+](https://img.shields.io/badge/hermes-%3E%3D0.18.0-purple)](https://github.com/HermesAgent/hermes)
[![Tests](https://img.shields.io/badge/tests-142%20cases-brightgreen)](tests/)

---

## Why This Project Exists

DeepSeek V4 has several unique API-layer and model-layer physical characteristics (reasoning_content structure, DSML tool calling format, Quick Instruction routing, reasoning effort control), but generic Agent frameworks don't optimize for these. Meanwhile, Agent engineering practices (cognitive gating, constraint immunity, intent routing) also lack systematic implementation.

Built on the Hermes Agent Plugin system, this project translates DeepSeek's physical properties into runnable Agent capabilities through a three-layer architecture of plugins, an independent context engine, and a merged microservice. It does not modify a single line of Hermes core code.

## Implemented Core Features

- ✅ **Cognitive Gate** (I-02 Bidirectional Primitives + I-08 Scope Control): Automatically injects L1 honor/shame values, L2 thinking patterns, and L3 exclusion list into every conversation turn
- ✅ **Constraint Immune System** (I-01 Hard Constraint Detection + Periodic Audit): Detects constraints like "must not / cannot", automatically logs violations, and runs daily cron audits
- ✅ **Intent Router** (I-10 7+1 Classification + Policy Binding): Keyword matching identifies 7+1 user intent types, binding different interview depth, Plan granularity, review standards, and execution modes
- ✅ **Tool Quality Assessment** (post_tool_call content integrity check): Automatically validates results of write/read/bash tool calls, intercepts empty results and exceptions
- ✅ **Session Learning** (I-09 Skill Proposal): Identifies reusable Skill patterns in long conversations and appends them to feedback-lessons.md
- ✅ **Daily Reflection**: Reads state.db via daily cron to count conversation turns and Token consumption, generates reflection reports in reflections/
- ✅ **Intent-to-Context Routing** (I-17 Intent-Based Dynamic Hints): Injects high-complexity reasoning hints for architecture/research/collaboration tasks and medium-complexity hints for refactor/new/medium tasks based on I-10 intent classification. Note: API parameter `reasoning_effort` is not used due to Hermes hook protocol limitations; context text injection is used instead
- ✅ **Timeliness Injection** (I-18 Degraded Fallback): Automatically injects current date and time on the first conversation turn. Note: API rejects `role=latest_reminder` (400 InvalidParameter); degraded to context text injection
- ✅ **Subtask Watch**: Tracks subagent_start/subagent_stop events, records each subtask's start, end, and result
- ✅ **Context Compression Engine** (I-03/I-04/I-07/I-13 Independent Context Engine Plugin): Uses DeepSeek API for independent context compression, does not depend on Hermes auxiliary_client
- ✅ **Harness Server Merged Service** (I-06/I-11/I-12 Three-in-One): Single FastAPI service + single SQLite, registers 9 tools exposed to LLM via `ctx.register_tool()`:
  - plan_create/plan_update_step/plan_cascade/plan_status (I-06 Cascading Planning)
  - memory_tag/memory_query/memory_filter (I-12 Memory Tagging + Lambda Filtering)
  - checkpoint_create/checkpoint_review (I-11 Checkpoint Review)

## Architecture (3 Layers)

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Hermes Plugin (plugins/deepseek-harness/)         │
│  10 Python files · 8 Hook points · 9 registered tools · v2.2│
│  pre_llm_call(5) + post_tool_call + on_session_end          │
│  + subagent_start + subagent_stop + 9 tools                 │
├──────────────────────────────────────────────────────────────┤
│  Layer 2: Context Engine Plugin (plugins/deepseek-context/) │
│  Independent LLM client · no Hermes auxiliary_client dep     │
│  I-03/I-04/I-07/I-13 four patterns implemented here         │
├──────────────────────────────────────────────────────────────┤
│  Layer 3: Harness Server (mcp/harness_server/)              │
│  Single FastAPI service · Single SQLite · Port 8200         │
│  I-06 Cascading Planning + I-12 Memory Tagging              │
│  + I-11 Checkpoint Review                                   │
│  9 tools exposed to LLM via ctx.register_tool()              │
└──────────────────────────────────────────────────────────────┘
```

### Layer 1: Hermes Plugin

`plugins/deepseek-harness/` contains 10 files injected through 8 Hook points + 9 tools:

| File | Hook | Trigger | Function |
|------|------|---------|----------|
| gate.py | pre_llm_call | Every LLM call | Cognitive reminder + MAP navigation |
| intent_router.py | pre_llm_call | Every LLM call | 7+1 intent classification + policy binding + exclusion list |
| reasoning_effort.py | pre_llm_call | First turn | Intent-to-context routing (I-17) |
| latest_reminder.py | pre_llm_call | First turn | Timeliness injection (I-18 degraded fallback) |
| immune_audit.py | pre_llm_call | Optional first turn | Constraint violation detection reminder |
| assessor.py | post_tool_call | After every tool call | Content integrity check |
| learner.py | on_session_end | At session end | Skill proposal appended to feedback log |
| subagent_watch.py | subagent_start/stop | On subtask start/stop | Records subtask status and result |
| tools.py | register_tool(×9) | Plugin registration | 9 tools exposed to LLM (I-06/I-11/I-12) |

### Layer 2: Context Engine Plugin

`plugins/deepseek-context/` is an independent LLM client plugin that calls the DeepSeek API directly, bypassing the Hermes auxiliary_client mechanism. It handles context compression, summarization, and structural reorganization (I-03 outer compression / I-04 time decay / I-07 inner compression / I-13 structural compression).

### Layer 3: Harness Server

`mcp/harness_server/` is a single FastAPI service that merges the original plan-engine, memory-tagger, and checkpoint-review into one. It exposes 9 tools to the LLM through `ctx.register_tool()`:

- **plan** endpoints (I-06): plan_create / plan_update_step / plan_cascade / plan_status
- **memory** endpoints (I-12): memory_tag / memory_query / memory_filter
- **checkpoint** endpoints (I-11): checkpoint_create / checkpoint_review

Single SQLite persistence (`~/.hermes/mcp/harness.db`), auto-launched during plugin registration.

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
│   ├── deepseek-harness/          # Main plugin (10 files, 8 hooks, 9 tools, v2.2)
│   │   ├── plugin.yaml            # Plugin declaration + I-01~I-18 pattern mapping
│   │   ├── __init__.py            # Registration entry (8 handlers + 9 tools)
│   │   ├── gate.py                # Cognitive gate (I-02 + I-08)
│   │   ├── intent_router.py       # Intent router (I-10)
│   │   ├── reasoning_effort.py    # Intent-to-context routing (I-17)
│   │   ├── latest_reminder.py     # Timeliness injection (I-18 degraded)
│   │   ├── immune_audit.py        # Constraint audit (I-01)
│   │   ├── assessor.py            # Tool quality assessment
│   │   ├── learner.py             # Session learning (I-09)
│   │   ├── subagent_watch.py      # Subtask watch
│   │   ├── tools.py               # 9 tool registrations (I-06/I-11/I-12)
│   │   └── strategies.yaml        # 7+1 intent strategy config
│   └── deepseek-context/          # Context engine plugin (independent LLM client)
│       ├── plugin.yaml
│       ├── __init__.py
│       ├── compressor.py          # I-03/I-04/I-07/I-13 compression
│       └── config.yaml
├── mcp/
│   └── harness_server/            # Merged service (I-06+I-11+I-12, port 8200)
│       ├── server.py, models.py, storage.py, config.yaml
├── scripts/
│   ├── install.sh                 # One-click install + auto backup
│   └── daily-reflection.sh        # Daily reflection (cron)
├── crons/
│   └── immune-audit.cron          # I-01 periodic constraint audit (daily 3:00)
├── tests/                         # pytest unit tests (142 cases)
├── docs/research/                 # Research documentation
├── README.md
├── README_EN.md
└── LICENSE                        # MIT
```

## Agent Engineering Patterns + DeepSeek V4 Physical Properties

| ID | Pattern Name | Status | Description |
|----|-------------|--------|-------------|
| I-01 | Hard Constraint Detection & Periodic Audit | ✅ | Parses "must not / cannot" instructions, logs violations, daily cron audit report |
| I-02 | Bidirectional Primitives (Affirmative + Negative) | ✅ | Three-layer cognitive architecture: L1 honor/shame values + L2 thinking patterns + L3 exclusion list |
| I-03 | Outer Context Compression | ✅ | Context Engine produces compressed summaries of raw conversation history |
| I-04 | Time-Decay Context Ordering | ✅ | Recent content retains detail, older content is automatically summarized |
| I-05 | Memory Tagging Middle Layer | ✅ | Memory Tagger service (original I-12 ID, later split into standalone service) |
| I-06 | Cascading Plan Correction | ✅ | harness_server plan_create/update_step/cascade/status tools, auto cascading impact analysis |
| I-07 | Inner Context Compression | ✅ | Context Engine performs structural compression at the system prompt level |
| I-08 | Scope Control (Exclusion List) | ✅ | Layer 1 Metis reverse questioning, auto-generates "not doing this time" exclusion list |
| I-09 | Skill Proposal & Auto Learning | ✅ | Detects reusable Skill patterns before long conversations end, appends to feedback log |
| I-10 | 7+1 Intent Classification & Policy Binding | ✅ | refactor/new/medium/collaboration/architecture/research/simple + spec_driven fallback |
| I-11 | Checkpoint Snapshot Review | ✅ | harness_server checkpoint_create/review tools, snapshot comparison + adjustment suggestions |
| I-12 | Memory Lambda Function Filtering | ✅ | harness_server memory_tag/query/filter tools, lambda expression filtering |
| I-13 | Structural Context Compression | ✅ | Context Engine selects compression strategy by data structure (code/config/docs) |
| I-14 | Provider-Aware Reasoning Strip | ❌ Removed | Dead code (hook passes copy, mutation ineffective) + design conflict with V4 API (tool-call turns require reasoning_content echo-back) |
| I-15 | DSML Tool Call Optimization | ⚪ Not needed | DeepSeek server auto-converts to OpenAI format; no client-side parsing needed (spike verified) |
| I-16 | Quick Instruction Routing | 🔲 Not feasible | V4 internal mechanism; not available via OpenAI-compatible API, replaced by I-10 intent routing |
| I-17 | Intent-to-Context Routing | ✅ | Injects reasoning hints based on I-10 intent classification. Note: API parameter `reasoning_effort` not used due to hook protocol limits |
| I-18 | Latest Reminder Injection (Degraded) | ✅ | Injects date/time on first turn. Note: API rejects `role=latest_reminder` (400), degraded to context injection |

All feasible patterns are implemented. I-14 removed due to technical limitations, I-15 handled server-side, I-16 not available via API.

## Roadmap

- ✅ **v1.0 Foundation Plugin**: Cognitive gate + quality assessment + learning summary + subtask watch (completed)
- ✅ **v2.0 Architecture**: Plugin + Context Engine + Microservice (completed)
- ✅ **v2.1 V4 Feature Validation**: Spike verified I-15~I-18 feasibility + implemented I-17/I-18 (completed)
- ✅ **v2.2 Fixes & Merger**: Removed I-14 dead code, merged 3 MCP into 1 + ctx.register_tool connection, corrected I-18 docstring and I-15 paper (completed)
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

**How is the Harness Server started?**
The harness_server process (port 8200) is auto-launched by `tools.py` via `_ensure_server_running()` during plugin registration. If the server is not running when a tool is called, it will be started automatically.

## Uninstall

```bash
hermes plugins disable deepseek-harness
rm -rf ~/.hermes/plugins/deepseek-harness/
```

Backup files created during installation (`*.bak.*`) are retained and must be cleaned up manually.

## License

MIT (c) 2026 yuanchenglu

---

> ⭐ If this project saved you time, give it a star so more people find the right way to use DeepSeek with Agents.
>
> *oh-my-deepseek-harness is an open source community project with no direct affiliation to DeepSeek or Hermes Agent.*
