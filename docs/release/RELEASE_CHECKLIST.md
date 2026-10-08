# Release Checklist（发布安全清单）

> SEC-001 发布安全门。每次发布前必须逐项核对并记录证据。未豁免
> High/Critical 依赖漏洞、SBOM 与 wheel 身份不一致、权限未最小化时**不得发布**。

## 1. Dependency / license / SBOM（SEC-001）

- [ ] 运行 `bash scripts/security/sbom.sh` 生成 `dist/sbom.json`
- [ ] SBOM 组件与 wheel 实际依赖一致（身份校验）
- [ ] 运行 `bash scripts/security/audit_deps.sh` 依赖漏洞扫描
- [ ] 无未豁免 High/Critical 漏洞（有则记录 Issue + 豁免理由 + 期限）
- [ ] 第三方许可证清单可追溯（MIT/Apache/BSD 等记录在案）

## 2. Release permissions（最小化）

- [ ] 发布工作流使用 OIDC / Trusted Publisher（无 registry token）
- [ ] 权限仅含必需的最小 scope（`contents: read` + 发布所需）
- [ ] 无长期有效凭证写入仓库

## 3. Artifact identity

- [ ] wheel/sdist 可重复构建（相同源码 → 相同哈希）
- [ ] 记录 exact commit SHA + artifact hash

## 4. Security gate（SECURITY.md）

- [ ] 私密漏洞报告通道可用
- [ ] 无开放 P0/P1 未处理（P1 需明确豁免）
- [ ] 已知缺陷均有 strict XFAIL 或已修复

## 5. Evidence

- [ ] 证据写入 `docs/testing/evidence/` 对应 Work ID
- [ ] 更新 traceability 行

## 6. Rollback

- [ ] 发布可撤回（新版本而非覆盖旧 tag）

> 本清单由 SECURITY.md 引用，是发布安全门的一部分。任何跳过项必须记录理由与 owner。

## v3.0.0 发布记录（2026-10-08）

| 检查项 | 结果 | 证据 |
|---|---|---|
| 依赖/许可证/SBOM | ✓（无未豁免 High/Critical；SBOM 身份一致） | `SEC-001.md`；`scripts/security/sbom.sh` |
| 发布权限最小化 | ✓（无 registry token；GitHub-only） | `.github/workflows/*`；`REL-005.md` |
| 制品身份（可重复构建） | ✓（RC 重建一致性 + 发布前 clean-venv 安装验证） | `REL-006.md`；`REL-008.md` §2–3 |
| 安全门（无开放 P0/P1） | ✓ | `STABLE-001.md` §1 |
| 证据与追踪 | ✓（GATE-G4/G5、M6 evidence、traceability 更新） | `docs/testing/evidence/*` |
| 回滚策略 | ✓（不可变发布；撤回=新版本） | `ROLLBACK.md` |