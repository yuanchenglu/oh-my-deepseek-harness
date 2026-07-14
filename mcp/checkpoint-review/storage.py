"""SQLite 存储层 — Checkpoint Review 持久化

负责：
- 数据库初始化和自动建表
- Checkpoint 插入与查询
- 按 plan_id 的 checkpoint_number 自动递增
- 按 plan_id 检索完整 Checkpoint 链
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from typing import Dict, List, Optional

from models import Checkpoint, CompletedStep

logger = logging.getLogger(__name__)

# 默认路径
DEFAULT_DB_PATH = os.path.expanduser("~/.hermes/mcp/checkpoint-review.db")


def _ensure_dir(path: str) -> None:
    """确保父目录存在"""
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)


class CheckpointStorage:
    """SQLite 存储层"""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        _ensure_dir(db_path)
        self._init_db()

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
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id    TEXT PRIMARY KEY,
                    plan_id          TEXT NOT NULL,
                    created_at       TEXT NOT NULL,
                    checkpoint_number INTEGER NOT NULL,
                    data_json        TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cp_plan_id
                ON checkpoints(plan_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cp_plan_number
                ON checkpoints(plan_id, checkpoint_number)
            """)
            conn.commit()
            logger.info("数据库初始化完成: %s", self.db_path)
        except sqlite3.Error as e:
            logger.error("数据库初始化失败: %s", e)
            raise
        finally:
            conn.close()

    # ── 查询 ────────────────────────────────────────────────

    def _get_next_number(self, plan_id: str) -> int:
        """获取 plan_id 的下一个 checkpoint_number"""
        conn = self._connection()
        try:
            row = conn.execute(
                "SELECT COALESCE(MAX(checkpoint_number), 0) AS max_num "
                "FROM checkpoints WHERE plan_id = ?",
                (plan_id,),
            ).fetchone()
            return (row["max_num"] if row["max_num"] else 0) + 1
        finally:
            conn.close()

    def insert(self, checkpoint: Checkpoint) -> str:
        """插入一个 Checkpoint，返回 checkpoint_id"""
        conn = self._connection()
        try:
            data_json_str = checkpoint.model_dump_json()
            conn.execute(
                "INSERT INTO checkpoints "
                "(checkpoint_id, plan_id, created_at, checkpoint_number, data_json) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    checkpoint.checkpoint_id,
                    checkpoint.plan_id,
                    checkpoint.created_at,
                    checkpoint.checkpoint_number,
                    data_json_str,
                ),
            )
            conn.commit()
            logger.info(
                "Checkpoint 已保存: %s (plan=%s, #%d)",
                checkpoint.checkpoint_id,
                checkpoint.plan_id,
                checkpoint.checkpoint_number,
            )
            return checkpoint.checkpoint_id
        except sqlite3.Error as e:
            logger.error("Checkpoint 保存失败: %s", e)
            raise
        finally:
            conn.close()

    def get(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """按 checkpoint_id 查询单个 Checkpoint"""
        conn = self._connection()
        try:
            row = conn.execute(
                "SELECT * FROM checkpoints WHERE checkpoint_id = ?",
                (checkpoint_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_checkpoint(row)
        finally:
            conn.close()

    def get_chain(self, plan_id: str) -> List[Checkpoint]:
        """按 plan_id 获取完整 Checkpoint 链（按 checkpoint_number 升序）"""
        conn = self._connection()
        try:
            rows = conn.execute(
                "SELECT * FROM checkpoints WHERE plan_id = ? "
                "ORDER BY checkpoint_number ASC",
                (plan_id,),
            ).fetchall()
            return [self._row_to_checkpoint(r) for r in rows]
        finally:
            conn.close()

    def get_chain_metadata(self, plan_id: str) -> List[Dict]:
        """获取 Checkpoint 链的元数据（精简版，不含 data_json）"""
        conn = self._connection()
        try:
            rows = conn.execute(
                "SELECT checkpoint_id, plan_id, created_at, checkpoint_number "
                "FROM checkpoints WHERE plan_id = ? "
                "ORDER BY checkpoint_number ASC",
                (plan_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def count_by_plan(self, plan_id: str) -> int:
        """统计指定 Plan 的 Checkpoint 数量"""
        conn = self._connection()
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM checkpoints WHERE plan_id = ?",
                (plan_id,),
            ).fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    def count_all(self) -> int:
        """总 Checkpoint 数量"""
        conn = self._connection()
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM checkpoints").fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    # ── 内部方法 ────────────────────────────────────────────

    @staticmethod
    def _row_to_checkpoint(row: sqlite3.Row) -> Checkpoint:
        """SQLite 行 → Checkpoint"""
        data = json.loads(row["data_json"])
        # 重建 CompletedStep 列表
        steps = [CompletedStep(**s) for s in data.get("completed_steps_summary", [])]
        return Checkpoint(
            checkpoint_id=data["checkpoint_id"],
            plan_id=data["plan_id"],
            created_at=data["created_at"],
            checkpoint_number=data["checkpoint_number"],
            current_goal=data["current_goal"],
            completed_steps_summary=steps,
            unexpected_findings=data.get("unexpected_findings", []),
            remaining_plan=data.get("remaining_plan", []),
            purpose=data.get("purpose", "step_threshold"),
        )
