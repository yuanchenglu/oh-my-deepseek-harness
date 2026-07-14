"""I-01 定期约束审计——读取约束违反记录，生成审计报告和 Skill 草案。"""

import datetime
import logging
import os
import re
from collections import Counter
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_VIOLATIONS_FILE = os.path.expanduser("~/.hermes/memories/constraint-violations.md")
_REFLECTIONS_DIR = os.path.expanduser("~/.hermes/reflections/")


def run_immune_audit() -> Dict[str, any]:
    """读取 constraint-violations.md，统计高频违反，输出审计报告。
    
    Returns:
        {"status": "ok"|"empty"|"error", "report_path": str, "violation_count": int, "high_frequency": list}
    """
    if not os.path.exists(_VIOLATIONS_FILE):
        logger.info("[I-01] 约束审计：无违反记录文件，跳过")
        return _empty_report("无约束违反记录文件")
    
    try:
        with open(_VIOLATIONS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
    except Exception as e:
        logger.warning("[I-01] 读取违反记录失败: %s", e)
        return _empty_report(f"读取失败: {e}")
    
    if not content:
        return _empty_report("约束违反记录为空")
    
    # 解析违反记录（每行格式：时间 | 约束 | 证据 | 工具）
    violations = _parse_violations(content)
    
    # 统计高频违反约束（过去 7 天，同一条约束违反 ≥ 3 次）
    recent = _filter_recent(violations, days=7)
    constraint_counter = Counter(v["constraint"] for v in recent)
    high_freq = [
        {"constraint": constraint, "count": count}
        for constraint, count in constraint_counter.items()
        if count >= 3
    ]
    
    # 为高频违反生成 Skill 草案
    skill_drafts = []
    for item in high_freq:
        skill_drafts.append(_generate_skill_draft(item["constraint"]))
    
    # 输出审计报告
    report = _format_report(recent, high_freq, skill_drafts)
    report_path = _write_report(report)
    
    return {
        "status": "ok",
        "report_path": report_path,
        "violation_count": len(violations),
        "recent_count": len(recent),
        "high_frequency": high_freq,
        "skill_drafts": skill_drafts
    }


def _empty_report(reason: str) -> Dict[str, any]:
    report_path = _write_report(f"# 免疫系统审计报告\n\n**状态**: 无审计内容\n**原因**: {reason}\n")
    return {"status": "empty" if "为空" in reason else "error", "report_path": report_path, "violation_count": 0, "high_frequency": []}


def _parse_violations(content: str) -> List[Dict[str, str]]:
    """从 Markdown 文本中解析违反记录条目。
    
    格式示例：
    - [2026-07-14 10:30] 约束: 不能修改配置文件 | 证据: write 调用了 /etc/config.yaml | 工具: write
    """
    entries = []
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # 尝试匹配格式：- [日期时间] 约束: X | 证据: Y | 工具: Z
        m = re.match(r'- \[([^\]]+)\]\s*约束:\s*([^|]+)\s*\|\s*证据:\s*([^|]+)\s*(?:\|\s*工具:\s*(\S+))?', line)
        if m:
            entries.append({
                "timestamp": m.group(1).strip(),
                "constraint": m.group(2).strip(),
                "evidence": m.group(3).strip(),
                "tool": m.group(4).strip() if m.group(4) else ""
            })
    return entries


def _filter_recent(violations: List[Dict], days: int = 7) -> List[Dict]:
    """只保留最近 days 天的记录。"""
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    return [v for v in violations if v.get("timestamp", "").startswith(tuple(str(y) for y in range(2020, 2030))) and v["timestamp"][:10] >= cutoff]


def _generate_skill_draft(constraint_text: str) -> Dict[str, str]:
    """为高频违反的约束生成 Skill 草案。
    
    将约束转换为可检查的 Skill 草案格式。
    """
    skill_name = "audit-" + constraint_text.replace(" ", "-").replace("不要", "no-").replace("不能", "no-")[:30]
    skill_name = re.sub(r'[^a-zA-Z0-9_-]', '', skill_name).lower().rstrip('-')
    if not skill_name:
        skill_name = f"audit-constraint-{abs(hash(constraint_text)) % 1000:03d}"
    
    return {
        "skill_name": skill_name,
        "trigger": f"检测到高频约束违反: {constraint_text}",
        "check_logic": f"在执行任务前，检查当前操作是否涉及「{constraint_text}」，如果命中则拦截并提醒用户。"
    }


def _format_report(recent, high_freq, skill_drafts) -> str:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# 免疫系统审计报告",
        f"**生成时间**: {now}",
        f"**近期违反记录**: {len(recent)} 条（过去 7 天）",
        f"**高频违反约束**: {len(high_freq)} 个",
        "",
        "## 高频违反约束",
    ]
    
    for item in high_freq:
        lines.append(f"- **{item['constraint']}** — 违反 {item['count']} 次")
    
    lines.extend(["", "## 生成的 Skill 草案"])
    for draft in skill_drafts:
        lines.extend([
            f"### {draft['skill_name']}",
            f"- 触发条件: {draft['trigger']}",
            f"- 检查逻辑: {draft['check_logic']}",
            ""
        ])
    
    if not high_freq:
        lines.append("（无高频违反约束，无需生成 Skill）")
    
    return "\n".join(lines)


def _write_report(content: str) -> str:
    os.makedirs(_REFLECTIONS_DIR, exist_ok=True)
    filename = f"immune-audit-{datetime.datetime.now().strftime('%Y-%m-%d')}.md"
    path = os.path.join(_REFLECTIONS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content + "\n")
    logger.info("[I-01] 审计报告已写入: %s", path)
    return path
