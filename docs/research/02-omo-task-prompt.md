# OMO 规划者任务 Prompt（小路发给 OMO 的原始提示词）

> 以下是小路直接发给 OMO 规划者的消息，完整复制即可。

---

小路说：

## 任务：oh-my-deepseek-harness v2 实施规划

### 背景

我们已在 Hermes 0.18 上做了一个 oh-my-deepseek-harness 插件，目前实现了 4 个 hook（认知门控、质量评估、学习总结、子任务监控），对应约 3-4 个设计模式的初级版本。

现在要升级到 v2，把 **14 个创新设计模式**（I-01 到 I-14）全部以 **Plugin + MCP + Skills + Cron** 的方式在 Hermes 上落地，**不改一行 Hermes 核心代码**。

### 输入材料

1. **调研报告**（基于 Hermes 源码 + 论文数据库的逐项可行性评估）：
   `/Volumes/Doc/Code/oh-my-deepseek-harness/docs/research/01-plugin-feasibility-research.md`

2. **14 个设计模式的理论原文**（以下所有文件，**必须逐篇阅读**）：
   `/Volumes/Doc/llm-harness-agent/zh/innovations/01-agent-immune-system.md`
   `/Volumes/Doc/llm-harness-agent/zh/innovations/02-bidirectional-agent.md`
   `/Volumes/Doc/llm-harness-agent/zh/innovations/03-attention-budget.md`
   `/Volumes/Doc/llm-harness-agent/zh/innovations/04-kv-cache-prefix.md`
   `/Volumes/Doc/llm-harness-agent/zh/innovations/05-document-kv-cache.md`
   `/Volumes/Doc/llm-harness-agent/zh/innovations/06-okr-planstep-cascade.md`
   `/Volumes/Doc/llm-harness-agent/zh/innovations/07-review-switching.md`
   `/Volumes/Doc/llm-harness-agent/zh/innovations/08-scope-creep.md`
   `/Volumes/Doc/llm-harness-agent/zh/innovations/09-skills-self-evolution.md`
   `/Volumes/Doc/llm-harness-agent/zh/innovations/10-intent-routing.md`
   `/Volumes/Doc/llm-harness-agent/zh/innovations/11-checkpoint-review.md`
   `/Volumes/Doc/llm-harness-agent/zh/innovations/12-memory-granularity.md`
   `/Volumes/Doc/llm-harness-agent/zh/innovations/13-byte-stable-prefix-architecture.md`
   `/Volumes/Doc/llm-harness-agent/zh/innovations/14-reasoning-content-stripping.md`

3. **总纲论文**（理解 14 个模式的内在逻辑和第一性原理）：
   `/Volumes/Doc/llm-harness-agent/zh/theory/paper.md`

4. **论文数据库**（理解 DeepSeek Harness 的学术定位）：
   `/Volumes/Doc/Code/deepseek-src/llmharnesagent-lite/references/papers-zh.md`

5. **现有 oh-my-deepseek-harness 插件源码**：
   `/Volumes/Doc/Code/oh-my-deepseek-harness/plugins/deepseek-harness/`

6. **Hermes 源码关键文件**（需要你读源码验证的地方）：
   - `agent/context_engine.py` — Context Engine 基类（插件化的入口）
   - `agent/context_compressor.py` — 默认 Context Engine 实现
   - `plugins/context_engine/__init__.py` — Context Engine 插件发现机制
   - `agent/smart_model_routing.py` — 内置模型路由（可扩展为意图路由）
   - `tools/mixture_of_agents_tool.py` — MoA 多模型并行推理
   - `tools/registry.py` — 工具注册中心

### 调研报告的结论摘要

| 维度 | 数据 |
|------|------|
| 完全可插件化 | 8 个（I-01, I-02, I-03, I-05, I-07, I-08, I-09, I-11） |
| 近似可行（有差距） | 4 个（I-04, I-06, I-10, I-12） |
| 需要核心修改 | 1 个（I-04 精确 KV Cache 分区——不做） |
| 调研未覆盖 | **2 个**（I-13 byte-stable prefix, I-14 reasoning stripping）——**需要你在审查中补充** |
| 最大发现 | Hermes v0.18 的 Context Engine Plugin 可替换整个压缩策略 |
| 唯一硬边界 | KV Cache 物理分区是推理引擎的能力，Hermes 不控制 |

### 你的任务

#### 1. 审查调研结论
- 逐项验证 14 个模式的可行性分类
- **特别审查 I-13 和 I-14**——这两个不在调研报告覆盖范围内
- 关注 I-07/I-04/I-10（这 3 个模式的评估在调研中被修正过，需要独立重审）
- 标注调研报告误判或漏掉的任何地方

#### 2. 实施计划
- Phase 1-4 的优先级排序和先决条件检查
- 每个 Phase 的 task 清单：文件路径 + 核心逻辑 + 依赖 + 测试路径
- 三个 MCP Server 的接口定义：plan-engine / memory-tagger / checkpoint-review
- Context Engine Plugin 的实现路径：fork 还是重写？约束检测和保护策略？
- 风险清单：兼容性、回退策略、与原生压缩器的冲突

#### 3. 工程量估算
- 每个 Phase 的预估人天
- 技术栈要求
- 测试策略

### 交付格式
- 产出物放到 `/Volumes/Doc/Code/oh-my-deepseek-harness/docs/plan/` 下
- 每项结论标注置信度（确定 / 80%+ / 不确定），不确定的说明下一步
- 对 Hermes 源码的论断必须标注文件路径和行号
- 发现调研报告有错误时，在计划中醒目标注：**「调研报告修正」** 原来 X，实际是 Y，原因是 Z
