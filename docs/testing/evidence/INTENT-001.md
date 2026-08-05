# INTENT-001 Evidence - Intent Routing Fixes

- Work ID: `INTENT-001`
- Canonical Issue: #41
- Dependency: CON-001 complete
- Status: **Complete**
- Implementation baseline: `develop@master`
- Implementation branch: `feat/intent-001-routing`
- Next: M3 完成（10/10）→ G3 Gate

## 1. Problem

低置信路径不可达、否定语义误判（"不要重构"判 refactor）、显式用户意图
无法覆盖自动路由、多类并列时置信度不够低。

## 2. Implementation

- `classify_intent` 加否定语义检测（TC-INTENT-006）：关键词前 3 字含否定词
  （不/不要/别/无需/勿/莫）则抑制该关键词匹配。
- 显式用户意图优先（TC-INTENT-005）：`_find_explicit_intent` 匹配
  "按/用/以 X 意图" 模式，返回已知意图名，confidence 1.0。
- 置信度阈值 0.5 → 0.6（TC-INTENT-003）：并列/低置信回退 spec_driven。
- `_keyword_match_score` 收紧 CJK 部分匹配阈值 0.7，防字符碎片假阳性。

## 3. CI evidence

PR #109:
- test (3.10): SUCCESS
- test (3.11): SUCCESS
- test (3.12): SUCCESS

## 4. TC coverage

| TC ID | Description | Tests | Status |
|---|---|---|---|
| TC-INTENT-003 | 多类并列 → neutral/default | `TestConfidenceTie` | PASS |
| TC-INTENT-005 | 用户 override | `TestExplicitOverride` | PASS |
| TC-INTENT-006 | 否定语义不误判 | `TestNegationSemantics` | PASS |
| TC-INTENT-008 | 无效策略 YAML → 安全默认 | `TestInvalidYaml` | PASS |

Local: test_intent_router.py 31 passed.

## 5. FR coverage

| FR ID | Description | Status |
|---|---|---|
| FR-INTENT-001~007 | 意图分类 + 策略绑定 | Covered |

## 6. Authorized paths

| Path | Status |
|---|---|
| `src/deepseek_harness/intent_router.py` | Modified (否定/override/阈值) |
| `src/deepseek_harness/resources/strategies.yaml` | Unchanged |
| `tests/test_intent_router.py` | Modified (TC-INTENT-003/005/006/008) |

## 7. Definition of Done

- [x] 低置信路径可达（阈值 0.6）
- [x] 否定语义正确处理（不因关键词误判）
- [x] 显式用户分类优先于自动路由
- [x] 无效 YAML 安全默认
- [x] Required CI + traceability