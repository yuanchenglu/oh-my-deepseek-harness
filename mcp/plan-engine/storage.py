"""SQLite 存储层 — Plan Engine 持久化

负责：
- 数据库初始化和自动建表（plans + steps）
- Plan/Step CRUD
- 按 plan_id 查询完整步骤列表
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from models import AssociationStrength, OKRPlanStep, PlanStatus

logger = logging.getLogger(__name__)

# 默认路径
DEFAULT_DB_PATH = os.path.expanduser("~/.hermes/mcp/plan-engine.db")


def _ensure_dir(path: str) -> None:
    """确保父目录存在"""
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)


class PlanStorage:
    """SQLite 存储层"""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        _ensure_dir(db_path)
        self._init_db()

    # ── 连接管理 ────────────────────────────────────────────

    def _connection(self) -> sqlite3.Connection:
        """获取数据库连接（每次新建，确保线程安全）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        """初始化数据库表结构"""
        conn = self._connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    plan_id     TEXT PRIMARY KEY,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS steps (
                    step_id             TEXT PRIMARY KEY,
                    plan_id             TEXT NOT NULL,
                    text                TEXT NOT NULL,
                    key                 TEXT NOT NULL DEFAULT '',
                    status              TEXT NOT NULL DEFAULT 'pending',
                    parent_id           TEXT DEFAULT NULL,
                    dependency_ids_json TEXT NOT NULL DEFAULT '[]',
                    association_strength TEXT NOT NULL DEFAULT 'moderate',
                    FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_steps_plan_id
                ON steps(plan_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_steps_parent_id
                ON steps(parent_id)
            """)
            conn.commit()
            logger.info("数据库初始化完成: %s", self.db_path)
        except sqlite3.Error as e:
            logger.error("数据库初始化失败: %s", e)
            raise
        finally:
            conn.close()

    # ── Plan CRUD ──────────────────────────────────────────

    def create_plan(self, plan_id: str) -> bool:
        """创建 Plan 记录，返回是否成功"""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connection()
        try:
            conn.execute(
                "INSERT INTO plans (plan_id, created_at, updated_at) VALUES (?, ?, ?)",
                (plan_id, now, now),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.warning("Plan 已存在: %s", plan_id)
            return False
        finally:
            conn.close()

    def update_plan_timestamp(self, plan_id: str) -> None:
        """更新 Plan 的时间戳"""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connection()
        try:
            conn.execute(
                "UPDATE plans SET updated_at = ? WHERE plan_id = ?",
                (now, plan_id),
            )
            conn.commit()
        finally:
            conn.close()

    def get_plan_meta(self, plan_id: str) -> Optional[Dict]:
        """获取 Plan 元数据"""
        conn = self._connection()
        try:
            row = conn.execute(
                "SELECT * FROM plans WHERE plan_id = ?", (plan_id,)
            ).fetchone()
            if row:
                return {"plan_id": row["plan_id"], "created_at": row["created_at"], "updated_at": row["updated_at"]}
            return None
        finally:
            conn.close()

    # ── Step CRUD ──────────────────────────────────────────

    def insert_steps(self, plan_id: str, steps: List[OKRPlanStep]) -> int:
        """批量插入步骤，返回成功数"""
        conn = self._connection()
        try:
            data = []
            for s in steps:
                dep_json = json.dumps(s.dependency_ids, ensure_ascii=False)
                data.append((
                    s.step_id, plan_id, s.text, s.key,
                    s.status.value, s.parent_id, dep_json,
                    s.association_strength.value,
                ))
            conn.executemany(
                "INSERT OR REPLACE INTO steps "
                "(step_id, plan_id, text, key, status, parent_id, dependency_ids_json, association_strength) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                data,
            )
            conn.commit()
            return len(data)
        except sqlite3.Error as e:
            logger.error("批量插入步骤失败: %s", e)
            raise
        finally:
            conn.close()

    def update_step(self, step_id: str, **kwargs) -> bool:
        """更新步骤字段，返回是否找到并更新"""
        allowed = {"text", "key", "status", "parent_id", "dependency_ids", "association_strength"}
        fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not fields:
            return False

        conn = self._connection()
        try:
            set_clauses = []
            params = []
            for key, value in fields.items():
                if key == "dependency_ids":
                    set_clauses.append("dependency_ids_json = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                elif key == "status" and isinstance(value, PlanStatus):
                    set_clauses.append("status = ?")
                    params.append(value.value)
                elif key == "association_strength" and isinstance(value, AssociationStrength):
                    set_clauses.append("association_strength = ?")
                    params.append(value.value)
                else:
                    set_clauses.append(f"{key} = ?")
                    params.append(value)
            params.append(step_id)
            sql = f"UPDATE steps SET {', '.join(set_clauses)} WHERE step_id = ?"
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            logger.error("更新步骤失败: %s", e)
            raise
        finally:
            conn.close()

    def get_steps(self, plan_id: str) -> List[OKRPlanStep]:
        """获取 Plan 下的所有步骤"""
        conn = self._connection()
        try:
            rows = conn.execute(
                "SELECT * FROM steps WHERE plan_id = ? ORDER BY rowid",
                (plan_id,),
            ).fetchall()
            return [self._row_to_step(r) for r in rows]
        finally:
            conn.close()

    def get_step(self, step_id: str) -> Optional[OKRPlanStep]:
        """获取单个步骤"""
        conn = self._connection()
        try:
            row = conn.execute(
                "SELECT * FROM steps WHERE step_id = ?", (step_id,)
            ).fetchone()
            return self._row_to_step(row) if row else None
        finally:
            conn.close()

    def get_step_plan_id(self, step_id: str) -> Optional[str]:
        """获取步骤所属的 plan_id"""
        conn = self._connection()
        try:
            row = conn.execute(
                "SELECT plan_id FROM steps WHERE step_id = ?", (step_id,)
            ).fetchone()
            return row["plan_id"] if row else None
        finally:
            conn.close()

    # ── 内部方法 ───────────────────────────────────────────

    @staticmethod
    def _row_to_step(row: sqlite3.Row) -> OKRPlanStep:
        """SQLite 行 → OKRPlanStep"""
        try:
            dep_ids = json.loads(row["dependency_ids_json"]) if row["dependency_ids_json"] else []
        except (json.JSONDecodeError, TypeError):
            dep_ids = []
        return OKRPlanStep(
            step_id=row["step_id"],
            text=row["text"],
            key=row["key"] or "",
            status=PlanStatus(row["status"]),
            parent_id=row["parent_id"],
            dependency_ids=dep_ids,
            association_strength=AssociationStrength(row["association_strength"]),
        )
