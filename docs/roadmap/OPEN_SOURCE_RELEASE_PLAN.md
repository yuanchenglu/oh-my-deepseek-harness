# 开源发布迭代计划

- 适用分支：`develop`
- 规划目标：达到真实可安装、可使用、可贡献的 Open-source Beta
- 核心约束：不新增 Innovation 编号，不扩展新平台，不做 UI，不做云服务
- 建议目标版本：`v0.3.0-beta` → `v0.4.0-beta` → `v1.0.0`

## 1. 第一性目标

项目当前不缺功能点，缺少的是完整产品闭环。接下来所有迭代只回答四个问题：

1. 用户能否安装并启动？
2. 核心优化是否会损坏用户数据或状态？
3. 出错时用户能否诊断和恢复？
4. 外部贡献者能否在不理解全部代码的情况下验证修改？

不直接提高这四项的工作不进入近期 Roadmap。

## 2. 发布策略

### 版本语义

当前代码成熟度与 `2.x stable` 语义不匹配。建议：

- 下一版本使用明确 Beta 标签；
- 可以选择 `v0.3.0-beta` 重置成熟度，也可以保留 `v2.3.0-beta`，但 README 必须明确实验状态；
- `v1.0.0` 只用于完成真实安装和用户验证后的稳定版。

### 分支策略

- `master`：可发布基线；
- `develop`：默认开发和文档分支；
- `fix/<scope>`：P0/P1 修复；
- `test/<scope>`：测试基础设施；
- 所有变更通过 PR 合入 `develop`；
- Release Candidate 再由 `develop` 合入 `master`。

## 3. Milestone 0：规格与质量基线

状态：本次工作完成主体。

### 产出

- [x] Code Review；
- [x] 产品架构；
- [x] 技术架构；
- [x] 完整 PRD；
- [x] 测试计划；
- [x] 已知缺陷回归测试；
- [x] `develop` CI Matrix；
- [ ] 首次 CI 完整测试报告；
- [ ] 将 Code Review P0/P1 建立 GitHub Issues。

### Exit Criteria

文档中的需求 ID、测试 ID 和缺陷 ID 可互相追踪。

---

## 4. Milestone 1：Runtime Integrity

建议周期：第 1 周

### M1-1 Harness Server package 化

- 将 Server 转为可安装 package；
- 增加 `__main__.py` / Console Script；
- App Factory；
- 统一环境变量；
- 健康和 readiness；
- 日志文件；
- Process Supervisor；
- 停止和重启。

**不做**：拆微服务、Docker、远程部署。

### M1-2 Installer 闭环

- 安装完整 extras；
- 注册 Plugin/Context；
- 端口检查；
- Doctor；
- 幂等安装；
- 卸载；
- 临时 HOME E2E。

### M1-3 Context 数据完整性

- 修复 Merge 分支重复；
- Summary 失败完整 rollback；
- 受保护消息原样保留；
- Stable Message ID；
- Tool Pair Validator；
- 输出 Token 不降则 rollback；
- Secret Redaction 基础版。

### M1-4 Session 隔离

- SessionPolicyStore；
- Session End Cleanup；
- 并发测试；
- 移除模块级共享可变状态。

### Exit Criteria

- 所有 Context/Session strict xfail 转为通过；
- Clean install E2E 通过；
- Python Matrix 全绿；
- P0 数量为 0。

---

## 5. Milestone 2：Contract & Data Integrity

建议周期：第 2 周

### M2-1 单一契约源

- Pydantic Model 生成 Tool Schema；
- 统一错误 Envelope；
- 九个 Tool Contract Tests；
- 修复 `lambda`、Checkpoint required fields、Plan Status。

### M2-2 Memory 幂等

- 增加 content hash；
- Source identity 和 mtime；
- Import batch；
- 默认关闭 startup import；
- 增加 `memory_store`；
- 支持删除和 dry run。

### M2-3 Plan 不变量

- 更新后循环检测；
- 同 Plan 依赖验证；
- 自依赖和缺失依赖；
- 状态机；
- 创建/更新事务。

### M2-4 Checkpoint 一致性

- Plan 存在验证；
- completed IDs 验证；
- 并发编号事务；
- Review rule version。

### Exit Criteria

- Tool Contract 100%；
- Memory 重启导入重复率 0；
- Plan DAG 不变量测试通过；
- 所有 Data Integrity strict xfail 转为通过。

---

## 6. Milestone 3：Open-source Usability

建议周期：第 3 周

### M3-1 文档真实性

- README 能力分级：Stable/Beta/Experimental/Degraded/Removed；
- 删除绝对化宣传；
- 明确外部摘要数据边界；
- 安装、Doctor、卸载文档；
- Known Limitations；
- Troubleshooting。

### M3-2 版本与发布治理

- 统一或明确独立版本策略；
- DB/Config Schema version；
- Migration Policy；
- Release Checklist；
- Changelog 基于实际行为。

### M3-3 贡献者体验

- 标准 package，无动态源码 symlink；
- `make test` 或统一脚本；
- Ruff、类型检查、ShellCheck；
- Issue/PR 模板；
- Good First Issue 只选择低风险模块。

### M3-4 兼容性

- 明确 Hermes 版本；
- Linux/macOS；
- Python 3.10–3.12；
- DeepSeek API 配置验证。

### Exit Criteria

- 新贡献者根据 CONTRIBUTING 可在 30 分钟内跑完测试；
- README 每项主要能力有证据链接；
- Doctor 能覆盖常见安装故障；
- Beta Release Checklist 完成。

---

## 7. Milestone 4：Beta 验证

建议周期：第 4 周及以后

### 验证方式

- 至少 5 名非维护者安装；
- 至少 20 次真实长会话；
- 覆盖代码、研究、架构、简单任务；
- 记录压缩 rollback、Tool failure 和安装问题；
- 不收集 Prompt 原文，只收集用户主动提交的诊断信息。

### Beta Exit Criteria

- 0 个未关闭 P0；
- 真实用户安装成功率 ≥ 80%，失败均有明确根因；
- 无上下文数据损坏报告；
- 无跨 Session 污染报告；
- Tool 成功率 ≥ 95%；
- 文档可独立解决多数安装问题。

---

## 8. v1.0.0 Gate

必须全部满足：

- [ ] P0 = 0；
- [ ] P1 有明确处理结论；
- [ ] Python/Linux/macOS CI；
- [ ] Hermes 真实版本 E2E；
- [ ] Clean install / Upgrade / Uninstall；
- [ ] Context Property Tests；
- [ ] Session 并发隔离；
- [ ] Tool Contract 100%；
- [ ] DB Migration 测试；
- [ ] Secret Redaction 和隐私文档；
- [ ] 5+ 外部用户验证；
- [ ] 14 天无数据完整性 P0；
- [ ] README 与实际能力一致。

## 9. 明确不做列表

开源首版前不做：

- I-19 及以后 Innovation；
- Claude Code、Codex、OpenCode 多平台适配；
- Web UI / Desktop UI；
- 多 Agent 编排平台；
- 云 Memory；
- 用户账号；
- OAuth/RBAC；
- 多租户；
- 分布式服务；
- 自动 Skill 执行；
- LLM 自动生成复杂 DAG；
- 商业化功能。

## 10. 建议 Issue 拆分

### P0

1. `fix(context): preserve original messages when summary fails`
2. `fix(context): remove duplicate tail assembly`
3. `fix(context): enforce protected-message invariants`
4. `fix(session): isolate constraints by session_id`
5. `fix(runtime): package and reliably start harness server`
6. `fix(install): complete runtime installation and doctor`

### P1

7. `fix(contract): generate tool schemas from pydantic models`
8. `fix(memory): make imports idempotent`
9. `fix(audit): use JSONL event format`
10. `fix(plan): validate DAG on every update`
11. `fix(test): isolate HOME and remove import side effects`
12. `docs: align README claims with tested capabilities`

## 11. 资源分配原则

如果只有一名维护者：

- 70%：P0 修复和测试；
- 20%：安装、Doctor、文档；
- 10%：Issue/PR 维护；
- 0%：新增功能。

如果有外部贡献者，优先开放：

- 文档真实性；
- Contract Tests；
- Test Isolation；
- Doctor 检查项；
- Memory Import 幂等测试。

Context Integrity 和 Session State 由核心维护者负责审查。

## 12. 成功定义

项目真正开源成功的标志不是 Star 数或 Innovation 数量，而是：

> 一个陌生用户能从 README 安装，完成任务，遇到故障能诊断，卸载后不破坏数据；一个陌生贡献者能复现问题、添加测试并安全提交修改。
