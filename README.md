# oh-my-deepseek-harness

数字分身 Harness 层——基于 Hermes Agent Plugin 系统，不修改一行核心代码。

## 功能特性

- **认知门控**：每轮对话自动注入认知提醒（L1 荣辱观 + L2 思维方式）
- **质量评估**：工具调用后自动检查结果完整性
- **学习总结**：session 结束后自动记录经验教训
- **三省吾身**：每日 cron 生成反思报告
- **多机同步**：AIPC → MacBook Air 单向主从记忆同步
- **安全安装**：自动备份已有记忆，不覆盖不删除

## 安装

```bash
git clone https://github.com/bluth/oh-my-deepseek-harness
cd oh-my-deepseek-harness

# 先预览备份和迁移计划
bash scripts/install.sh --dry-run

# 确认无误后执行
bash scripts/install.sh

# 验证插件状态
hermes plugins list | grep deepseek-harness
```

## 目录结构

```
oh-my-deepseek-harness/
├── plugins/deepseek-harness/   # 数字分身 Plugin
│   ├── plugin.yaml         # 插件声明（5 个 Hook）
│   ├── __init__.py         # 注册入口
│   ├── gate.py             # 认知门控（pre_llm_call hook）
│   ├── assessor.py         # 质量评估（post_tool_call hook）
│   ├── learner.py          # 学习总结（on_session_end hook）
│   └── subagent_watch.py   # 子任务监控（subagent_start/stop hook）
├── scripts/
│   ├── install.sh          # 一键安装+备份+迁移
│   ├── sync-deepseek-harness.sh # AIPC→MacBook Air 同步
│   └── daily-reflection.sh # 每日三省吾身（cron 用）
├── tests/                  # pytest 单元测试
├── docs/                   # 文档
├── README.md
├── LICENSE                 # MIT
└── .gitignore
```

## 组件说明

| 组件 | Hook 类型 | 触发时机 | 功能 |
|------|-----------|---------|------|
| MAP.md | — | pre_llm_call 读取 | 记忆导航索引，仅存指针不存内容 |
| gate.py | pre_llm_call | 每轮 LLM 调用前 | 注入认知提醒 + MAP 导航 |
| assessor.py | post_tool_call | 每个工具调用后 | 检查结果内容完整性 |
| learner.py | on_session_end | session 结束时 | 追加经验教训到 feedback-lessons.md |
| subagent_watch.py | subagent_start/stop | 子任务启停时 | 记录子任务状态和结果 |
| sync-deepseek-harness.sh | cron | 每日 4AM | AIPC→MacBook 单向同步 |
| daily-reflection.sh | cron | 每日 5AM | 生成反思报告到 reflections/ |

## 卸载

```bash
hermes plugins disable deepseek-harness
rm -rf ~/.hermes/plugins/deepseek-harness/
```

注意：安装时创建的备份文件（`*.bak.*`）会保留，需手动清理。

## FAQ

**会修改 Hermes 核心代码吗？**
不会。全部使用 Hermes 官方 Plugin Hook 接口（pre_llm_call / post_tool_call / on_session_end / subagent_start / subagent_stop），这些接口已在源码中验证。Hermes 每日更新也不会产生 merge 冲突。

**会覆盖我已有的记忆吗？**
不会。安装前自动备份 SOUL.md、MEMORY.md、USER.md 为 `.bak.{timestamp}`，不删除原始内容。

**需要什么环境？**
- Hermes Agent ≥ v0.18.0
- Python ≥ 3.10
- rsync、sqlite3 CLI、pyyaml（可选，部分功能需要）

**和 MemOS 插件冲突吗？**
不冲突。彼此使用不同的 Plugin Hook 和文件路径，独立工作。

## License

MIT
