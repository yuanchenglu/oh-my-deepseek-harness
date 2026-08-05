# Release Notes - v3.0.0-beta.1

**oh-my-deepseek-harness** — DeepSeek 深度优化插件（14 项物理特性全激发）

## 版本

- 版本：`v3.0.0-beta.1`
- 基线：G0/G1/G2/G3 PASS，41/48 Work ID
- 产品成熟度：**Public Beta（首个 Beta 发布）**
- 许可：MIT

## 新特性（相对 review baseline）

### Plugin & 运行时
- Hermes v0.19.0 插件注册探针通过：5 个 Hook（pre_llm_call / post_tool_call /
  on_session_end / subagent_start / subagent_stop）+ 9 个 Runtime Tool
- 10 Tool 契约成型（memory_store 由 MEM-001 实现，Runtime 9 个可用）
- Session 策略隔离（SES-001）：按 session_id 隔离硬约束

### 规划引擎
- OKR Plan 创建/更新/级联/状态（plan_create / plan_update_step / plan_cascade /
  plan_status）
- Checkpoint 快照与审查（checkpoint_create / checkpoint_review）

### 记忆系统
- memory_store / Tag / Query / Filter（content hash、source identity、mtime）
- Markdown 记忆导入（import batch、λ 连续边界）

### 认知控制
- 认知门（cognitive gate）、意图路由（intent router）、推理强度控制、
  时效信息注入
- 约束审计（immune audit）+ 审计事件 JSONL 源（AUD-001）

### 质量与安全
- 三通道测试（fast/integration/release）+ 质量门（ruff/coverage/shellcheck）
- SBOM 生成 + 依赖审计 + Release Checklist（SEC-001）
- 安全边界验证（loopback-only、symlink 拒绝、SQL 注入免疫、权限 0700/0600）
- Beta 迁移 + 失败回滚（MIG-001）

## 已知限制（Known Limitations）

- Hermes 完整集成支持 Python 3.11–3.12；Python 3.10 仅 package/core CI
- 未提供远程多用户服务
- PyPI 发布按 REL-005 禁用；仅 GitHub Release

## 制品

- wheel + sdist + SHA256 + SBOM + provenance（同 commit）
- 详细见 Release Checklist 与 REL-006 evidence

## 安装

```bash
pip install oh-my-deepseek-harness==3.0.0b1
# 或从 GitHub Release 下载 wheel
```

## 反馈

- 报告问题：https://github.com/yuanchenglu/oh-my-deepseek-harness/issues
- 安全报告：SECURITY.md 私密通道
