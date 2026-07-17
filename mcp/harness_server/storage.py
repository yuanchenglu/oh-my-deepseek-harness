"""合并后的 SQLite 存储层 — Harness Server

本文件将 3 个原服务的存储层合并为一个，使用单个 SQLite 数据库文件
（~/.hermes/mcp/harness.db），包含 3 组表：

1. plans + steps       — Plan Engine 的 Plan 和步骤数据
2. memories            — Memory Tagger 的记忆条目
3. checkpoints         — Checkpoint Review 的快照数据

所有操作通过 HarnessStorage 类统一管理，内部按方法名前缀区分归属：
- create_plan / insert_steps / get_steps ...    （Plan 相关）
- insert_memory / query_memories / filter_by_lambda ...（Memory 相关）
- insert_checkpoint / get_checkpoint / get_checkpoint_chain ...（Checkpoint 相关）

设计说明：
- 每次操作都新建连接（sqlite3 连接很轻量），确保线程安全
- 开启 WAL 模式提升并发读性能
- 开启外键约束（steps 表引用 plans 表）
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .models import (
    AssociationStrength,
    Checkpoint,
    CompletedStep,
    MemoryEntry,
    MemoryLayer,
    OKRPlanStep,
    PlanStatus,
)

logger = logging.getLogger(__name__)

# 数据库默认路径：~/.hermes/mcp/harness.db
# 所有 3 组表都在这一个文件里，方便管理
DEFAULT_DB_PATH = os.path.expanduser("~/.hermes/mcp/harness.db")


def _ensure_dir(path: str) -> None:
    """确保给定路径的父目录存在，不存在则创建

    例如 path="~/.hermes/mcp/harness.db" 会创建 ~/.hermes/mcp/ 目录。
    """
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)


def _parse_datetime(text: str) -> datetime:
    """尝试多种格式解析日期时间字符串

    因为外部传入的时间格式可能不统一，这里依次尝试：
    1. 2025-01-15T08:30:00.123456Z  （带微秒和 Z 后缀）
    2. 2025-01-15T08:30:00Z          （不带微秒）
    3. 2025-01-15 08:30:00           （空格分隔）
    4. 2025-01-15                    （仅日期）

    所有格式都解析为 UTC 时间。如果全部失败，返回当前 UTC 时间。

    Args:
        text: 日期时间字符串

    Returns:
        解析后的 datetime 对象（带 UTC 时区信息）
    """
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    return datetime.now(timezone.utc)


class HarnessStorage:
    """统一的 SQLite 存储层，管理 Plan / Memory / Checkpoint 三组数据

    使用方法：
        storage = HarnessStorage()                    # 用默认路径
        storage = HarnessStorage("/path/to/db.db")    # 指定路径

        # Plan 相关
        storage.create_plan("plan_xxx")
        storage.insert_steps("plan_xxx", steps)

        # Memory 相关
        storage.insert_memory(entry)
        entries = storage.query_memories(tags=["python"])

        # Checkpoint 相关
        storage.insert_checkpoint(checkpoint)
        chain = storage.get_checkpoint_chain("plan_xxx")
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """初始化存储层

        Args:
            db_path: SQLite 数据库文件路径，默认 ~/.hermes/mcp/harness.db
        """
        self.db_path = db_path
        _ensure_dir(db_path)
        self._init_db()

    # ── 连接管理 ────────────────────────────────────────────

    def _connection(self) -> sqlite3.Connection:
        """获取一个新的数据库连接

        每次调用都创建新连接，确保线程安全。
        配置说明：
        - row_factory=Row: 让查询结果可以用 row["column"] 访问
        - WAL 模式: 提升并发读性能（多读单写）
        - foreign_keys=ON: 开启外键约束检查
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        """初始化所有 3 组表结构

        使用 CREATE TABLE IF NOT EXISTS，所以重复调用是安全的。
        """
        conn = self._connection()
        try:
            # ── 第 1 组：Plan Engine 表 ──────────────────
            # plans 表：存储 Plan 元数据（ID + 时间戳）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    plan_id     TEXT PRIMARY KEY,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                )
            """)
            # steps 表：存储每个 PlanStep 的完整数据
            # dependency_ids 用 JSON 字符串存储（因为 SQLite 没有数组类型）
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
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_steps_plan_id ON steps(plan_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_steps_parent_id ON steps(parent_id)"
            )

            # ── 第 2 组：Memory Tagger 表 ─────────────────
            # memories 表：存储每条记忆的内容、标签、层级
            # tags 用 JSON 字符串存储（因为 SQLite 没有数组类型）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    content     TEXT    NOT NULL,
                    tags        TEXT    NOT NULL DEFAULT '[]',
                    layer       TEXT    NOT NULL,
                    created_at  TEXT    NOT NULL,
                    source      TEXT    DEFAULT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_layer ON memories(layer)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at)"
            )

            # ── 第 3 组：Checkpoint Review 表 ──────────────
            # checkpoints 表：存储每个 Checkpoint 快照
            # data_json 存储完整的 Checkpoint 对象（JSON 序列化）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id    TEXT PRIMARY KEY,
                    plan_id          TEXT NOT NULL,
                    created_at       TEXT NOT NULL,
                    checkpoint_number INTEGER NOT NULL,
                    data_json        TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cp_plan_id ON checkpoints(plan_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cp_plan_number ON checkpoints(plan_id, checkpoint_number)"
            )

            conn.commit()
            logger.info("数据库初始化完成（3 组表）: %s", self.db_path)
        except sqlite3.Error as e:
            logger.error("数据库初始化失败: %s", e)
            raise
        finally:
            conn.close()

    # ════════════════════════════════════════════════════════════
    # Plan Engine CRUD 方法
    # ════════════════════════════════════════════════════════════

    def create_plan(self, plan_id: str) -> bool:
        """创建 Plan 记录

        Args:
            plan_id: Plan 唯一标识（UUID）

        Returns:
            True 表示创建成功，False 表示 Plan 已存在
        """
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
        """更新 Plan 的 updated_at 时间戳

        在步骤状态变更或级联修正后调用。

        Args:
            plan_id: Plan 唯一标识
        """
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
        """获取 Plan 元数据（不含步骤）

        Args:
            plan_id: Plan 唯一标识

        Returns:
            包含 plan_id / created_at / updated_at 的字典，不存在则 None
        """
        conn = self._connection()
        try:
            row = conn.execute(
                "SELECT * FROM plans WHERE plan_id = ?", (plan_id,)
            ).fetchone()
            if row:
                return {
                    "plan_id": row["plan_id"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            return None
        finally:
            conn.close()

    def insert_steps(self, plan_id: str, steps: List[OKRPlanStep]) -> int:
        """批量插入步骤

        Args:
            plan_id: 所属 Plan ID
            steps: 步骤列表

        Returns:
            成功插入的步骤数
        """
        conn = self._connection()
        try:
            data = []
            for s in steps:
                # dependency_ids 是列表，存为 JSON 字符串
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
        """更新步骤的字段

        只更新传入的字段（kwargs 中非 None 的字段）。
        支持的字段: text, key, status, parent_id, dependency_ids, association_strength

        Args:
            step_id: 步骤唯一标识
            **kwargs: 要更新的字段

        Returns:
            True 表示找到并更新了，False 表示步骤不存在或没有可更新字段
        """
        # 白名单过滤，防止 SQL 注入
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
                    # 列表 → JSON 字符串
                    set_clauses.append("dependency_ids_json = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                elif key == "status" and isinstance(value, PlanStatus):
                    # 枚举 → 字符串值
                    set_clauses.append("status = ?")
                    params.append(value.value)
                elif key == "association_strength" and isinstance(value, AssociationStrength):
                    # 枚举 → 字符串值
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
        """获取某个 Plan 下的所有步骤

        按 rowid（插入顺序）排序返回。

        Args:
            plan_id: Plan 唯一标识

        Returns:
            步骤列表，空 Plan 返回空列表
        """
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
        """获取单个步骤

        Args:
            step_id: 步骤唯一标识

        Returns:
            步骤对象，不存在则 None
        """
        conn = self._connection()
        try:
            row = conn.execute(
                "SELECT * FROM steps WHERE step_id = ?", (step_id,)
            ).fetchone()
            return self._row_to_step(row) if row else None
        finally:
            conn.close()

    def get_step_plan_id(self, step_id: str) -> Optional[str]:
        """获取步骤所属的 plan_id

        Args:
            step_id: 步骤唯一标识

        Returns:
            plan_id 字符串，步骤不存在则 None
        """
        conn = self._connection()
        try:
            row = conn.execute(
                "SELECT plan_id FROM steps WHERE step_id = ?", (step_id,)
            ).fetchone()
            return row["plan_id"] if row else None
        finally:
            conn.close()

    @staticmethod
    def _row_to_step(row: sqlite3.Row) -> OKRPlanStep:
        """将 SQLite 行转换为 OKRPlanStep 对象

        主要工作是把 JSON 字符串还原为列表，把字符串还原为枚举。

        Args:
            row: sqlite3.Row 查询结果行

        Returns:
            OKRPlanStep 对象
        """
        # 解析 dependency_ids（JSON 字符串 → 列表）
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

    # ════════════════════════════════════════════════════════════
    # Memory Tagger CRUD 方法
    # ════════════════════════════════════════════════════════════

    def insert_memory(self, entry: MemoryEntry, source: Optional[str] = None) -> int:
        """插入一条记忆

        Args:
            entry: 记忆条目对象
            source: 记忆来源（比如文件名），可选

        Returns:
            新插入记录的自增 ID
        """
        conn = self._connection()
        try:
            tags_json = json.dumps(entry.tags, ensure_ascii=False)
            created = entry.created_at.isoformat() if entry.created_at else (
                datetime.now(timezone.utc).isoformat()
            )
            cur = conn.execute(
                "INSERT INTO memories (content, tags, layer, created_at, source) "
                "VALUES (?, ?, ?, ?, ?)",
                (entry.content, tags_json, entry.layer.value, created, source),
            )
            conn.commit()
            return cur.lastrowid or 0
        finally:
            conn.close()

    def bulk_insert_memories(
        self, entries: List[MemoryEntry], source: Optional[str] = None,
    ) -> int:
        """批量插入记忆

        Args:
            entries: 记忆条目列表
            source: 记忆来源，可选

        Returns:
            成功插入的条数
        """
        conn = self._connection()
        try:
            data = []
            for e in entries:
                tags_json = json.dumps(e.tags, ensure_ascii=False)
                created = e.created_at.isoformat() if e.created_at else (
                    datetime.now(timezone.utc).isoformat()
                )
                data.append((e.content, tags_json, e.layer.value, created, source))
            conn.executemany(
                "INSERT INTO memories (content, tags, layer, created_at, source) "
                "VALUES (?, ?, ?, ?, ?)",
                data,
            )
            conn.commit()
            return len(data)
        finally:
            conn.close()

    def query_memories(
        self,
        tags: Optional[List[str]] = None,
        layer: Optional[MemoryLayer] = None,
        limit: int = 50,
    ) -> List[MemoryEntry]:
        """按标签和/或层级查询记忆

        tags 和 layer 同时使用时取交集（AND 关系）。
        tags 之间是 OR 关系（匹配任意一个标签即可）。

        Args:
            tags: 标签筛选列表（匹配任意一个）
            layer: 层级筛选
            limit: 返回条数上限

        Returns:
            记忆条目列表，按创建时间倒序排列
        """
        conn = self._connection()
        try:
            conditions: List[str] = []
            params: List[str] = []

            if layer is not None:
                conditions.append("layer = ?")
                params.append(layer.value)

            if tags:
                # 用 SQLite JSON1 扩展查询 JSON 数组中的标签
                # json_each(tags) 把 JSON 数组展开成多行，j.value 是每个元素
                tag_conditions = [
                    f"EXISTS (SELECT 1 FROM json_each(tags) AS j WHERE j.value = ?)"
                    for _ in tags
                ]
                conditions.append(f"({' OR '.join(tag_conditions)})")
                params.extend(tags)

            where = ""
            if conditions:
                where = "WHERE " + " AND ".join(conditions)

            sql = f"SELECT * FROM memories {where} ORDER BY created_at DESC LIMIT ?"
            params.append(str(limit))

            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_memory(r) for r in rows]
        finally:
            conn.close()

    def filter_by_lambda(self, lambda_value: float, limit: int = 50) -> List[MemoryEntry]:
        """按 λ 值过滤记忆

        λ 值决定注入哪些层级的记忆（见 MemoryLayer 枚举和 _lambda_to_layers）：
        - [0.0, 0.3] → 仅 constraint 层
        - [0.4, 0.7] → constraint + preference + decision
        - [0.8, 1.0] → 全部层级

        Args:
            lambda_value: λ 值 (0~1)
            limit: 返回条数上限

        Returns:
            过滤后的记忆条目列表
        """
        layers = self._lambda_to_layers(lambda_value)
        if not layers:
            return []

        placeholders = ",".join(["?" for _ in layers])
        conn = self._connection()
        try:
            sql = (
                f"SELECT * FROM memories "
                f"WHERE layer IN ({placeholders}) "
                f"ORDER BY created_at DESC LIMIT ?"
            )
            params: List[str] = list(layers) + [str(limit)]
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_memory(r) for r in rows]
        finally:
            conn.close()

    def count_by_layer(self) -> Dict[str, int]:
        """统计各层级的记忆数量

        Returns:
            字典: {"constraint": 5, "preference": 3, ...}
        """
        conn = self._connection()
        try:
            rows = conn.execute(
                "SELECT layer, COUNT(*) as cnt FROM memories GROUP BY layer"
            ).fetchall()
            return {r["layer"]: r["cnt"] for r in rows}
        finally:
            conn.close()

    def count_total_memories(self) -> int:
        """统计记忆总条数

        Returns:
            记忆总条数
        """
        conn = self._connection()
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM memories").fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    def get_layers_for_lambda(self, lambda_value: float) -> List[str]:
        """获取 λ 值对应的记忆层级列表

        Args:
            lambda_value: λ 值 (0~1)

        Returns:
            层级名称字符串列表，如 ["constraint", "preference"]
        """
        return self._lambda_to_layers(lambda_value)

    @staticmethod
    def _lambda_to_layers(lambda_value: float) -> List[str]:
        """λ 值到层级的映射（内部方法）

        这个映射规则对应 I-12 文档中的 Memory 粒度控制理论：
        - 低 λ：发散任务（创意/写作），只保留最关键的约束
        - 中 λ：混合任务（方案/分析），约束+偏好+决策
        - 高 λ：收敛任务（工程/部署），全量注入历史经验

        Args:
            lambda_value: λ 值 (0~1)

        Returns:
            层级名称列表
        """
        if lambda_value <= 0.3:
            return ["constraint"]
        elif lambda_value <= 0.7:
            return ["constraint", "preference", "decision"]
        else:
            return ["constraint", "preference", "style", "decision", "pattern"]

    @staticmethod
    def _row_to_memory(row: sqlite3.Row) -> MemoryEntry:
        """将 SQLite 行转换为 MemoryEntry 对象

        主要工作是把 JSON 字符串还原为标签列表，解析时间字符串。

        Args:
            row: sqlite3.Row 查询结果行

        Returns:
            MemoryEntry 对象
        """
        tags_raw = row["tags"] if row["tags"] else "[]"
        try:
            tags = json.loads(tags_raw)
        except (json.JSONDecodeError, TypeError):
            tags = []
        created = _parse_datetime(row["created_at"])
        return MemoryEntry(
            content=row["content"],
            tags=tags,
            layer=MemoryLayer(row["layer"]),
            created_at=created,
        )

    # ════════════════════════════════════════════════════════════
    # Checkpoint Review CRUD 方法
    # ════════════════════════════════════════════════════════════

    def _get_next_checkpoint_number(self, plan_id: str) -> int:
        """获取 plan_id 的下一个 checkpoint_number

        Checkpoint 编号在每个 Plan 内从 1 递增。
        用 COALESCE(MAX(checkpoint_number), 0) 处理 Plan 还没有 Checkpoint 的情况。

        Args:
            plan_id: Plan 唯一标识

        Returns:
            下一个编号（整数，>= 1）
        """
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

    def insert_checkpoint(self, checkpoint: Checkpoint) -> str:
        """插入一个 Checkpoint 快照

        Args:
            checkpoint: Checkpoint 对象

        Returns:
            checkpoint_id（与传入的相同）
        """
        conn = self._connection()
        try:
            # 整个 Checkpoint 对象序列化为 JSON 存储在 data_json 字段
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

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """按 checkpoint_id 查询单个 Checkpoint

        Args:
            checkpoint_id: Checkpoint 唯一标识

        Returns:
            Checkpoint 对象，不存在则 None
        """
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

    def get_checkpoint_chain(self, plan_id: str) -> List[Checkpoint]:
        """按 plan_id 获取完整 Checkpoint 链

        按 checkpoint_number 升序排列（从第 1 个到最新）。

        Args:
            plan_id: Plan 唯一标识

        Returns:
            Checkpoint 列表，空则返回空列表
        """
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

    def count_checkpoints_by_plan(self, plan_id: str) -> int:
        """统计指定 Plan 的 Checkpoint 数量

        Args:
            plan_id: Plan 唯一标识

        Returns:
            Checkpoint 数量
        """
        conn = self._connection()
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM checkpoints WHERE plan_id = ?",
                (plan_id,),
            ).fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    def count_all_checkpoints(self) -> int:
        """统计所有 Checkpoint 总数

        Returns:
            Checkpoint 总数
        """
        conn = self._connection()
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM checkpoints").fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    @staticmethod
    def _row_to_checkpoint(row: sqlite3.Row) -> Checkpoint:
        """将 SQLite 行转换为 Checkpoint 对象

        从 data_json 字段反序列化完整对象，包括重建 CompletedStep 列表。

        Args:
            row: sqlite3.Row 查询结果行

        Returns:
            Checkpoint 对象
        """
        data = json.loads(row["data_json"])
        # 重建 CompletedStep 列表（从原始字典列表）
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
