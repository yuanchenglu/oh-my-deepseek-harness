"""SQLite 存储层 — Memory Tagger 持久化

负责：
- 数据库初始化和自动建表
- MemoryEntry CRUD
- λ 过滤查询
- 从 Hermes Memory 目录（~/.hermes/memories/*.md）导入初始数据
"""

from __future__ import annotations

import glob
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from models import MemoryEntry, MemoryLayer

logger = logging.getLogger(__name__)

# 默认路径
DEFAULT_DB_PATH = os.path.expanduser("~/.hermes/mcp/memory-tagger.db")
DEFAULT_MEMORIES_DIR = os.path.expanduser("~/.hermes/memories/")


def _ensure_dir(path: str) -> None:
    """确保父目录存在"""
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)


def _parse_datetime(text: str) -> datetime:
    """尝试多种格式解析日期时间，失败时返回当前 UTC"""
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


class MemoryStorage:
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
                CREATE TABLE IF NOT EXISTS memories (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    content     TEXT    NOT NULL,
                    tags        TEXT    NOT NULL DEFAULT '[]',
                    layer       TEXT    NOT NULL,
                    created_at  TEXT    NOT NULL,
                    source      TEXT    DEFAULT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_layer
                ON memories(layer)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_created_at
                ON memories(created_at)
            """)
            conn.commit()
            logger.info("数据库初始化完成: %s", self.db_path)
        except sqlite3.Error as e:
            logger.error("数据库初始化失败: %s", e)
            raise
        finally:
            conn.close()

    # ── CRUD ────────────────────────────────────────────────

    def insert(self, entry: MemoryEntry, source: Optional[str] = None) -> int:
        """插入一条记忆，返回自增 ID"""
        conn = self._connection()
        try:
            import json
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

    def bulk_insert(
        self, entries: List[MemoryEntry], source: Optional[str] = None,
    ) -> int:
        """批量插入，返回成功数"""
        conn = self._connection()
        try:
            import json
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

    def query(
        self,
        tags: Optional[List[str]] = None,
        layer: Optional[MemoryLayer] = None,
        limit: int = 50,
    ) -> List[MemoryEntry]:
        """按标签和/或层级查询记忆"""
        conn = self._connection()
        try:
            conditions: List[str] = []
            params: List[str] = []

            if layer is not None:
                conditions.append("layer = ?")
                params.append(layer.value)

            if tags:
                import json
                placeholders = ["?" for _ in tags]
                # SQLite JSON1 扩展：tags 字段是 JSON 数组
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
            return [self._row_to_entry(r) for r in rows]
        finally:
            conn.close()

    def filter_by_lambda(self, lambda_value: float, limit: int = 50) -> List[MemoryEntry]:
        """按 λ 值过滤记忆

        λ 区间决定注入哪些层级：
        - [0.0, 0.3] → 仅 constraint
        - [0.4, 0.7] → constraint + preference + decision
        - [0.8, 1.0] → 全部层级
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
            return [self._row_to_entry(r) for r in rows]
        finally:
            conn.close()

    def count_by_layer(self) -> Dict[str, int]:
        """统计各层级记忆数量"""
        conn = self._connection()
        try:
            rows = conn.execute(
                "SELECT layer, COUNT(*) as cnt FROM memories GROUP BY layer"
            ).fetchall()
            return {r["layer"]: r["cnt"] for r in rows}
        finally:
            conn.close()

    def count_total(self) -> int:
        """总记忆条数"""
        conn = self._connection()
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM memories").fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    def get_layers_for_lambda(self, lambda_value: float) -> List[str]:
        """获取 λ 值对应的记忆层级列表"""
        return self._lambda_to_layers(lambda_value)

    # ── 导入 ────────────────────────────────────────────────

    def import_from_hermes(self, memories_dir: str = DEFAULT_MEMORIES_DIR) -> Tuple[int, int, int]:
        """从 Hermes Memory 目录导入 .md 文件

        Returns (imported, skipped, total_files)
        """
        if not os.path.isdir(memories_dir):
            logger.warning("Hermes Memory 目录不存在: %s", memories_dir)
            return 0, 0, 0

        md_files = glob.glob(os.path.join(memories_dir, "*.md"))
        total_files = len(md_files)

        imported = 0
        skipped = 0

        for filepath in md_files:
            try:
                ok, count = self._import_md_file(filepath)
                if ok:
                    imported += count
                else:
                    skipped += 1
            except Exception as e:
                logger.warning("导入文件失败 %s: %s", filepath, e)
                skipped += 1

        logger.info(
            "Hermes 导入完成: %d 条插入, %d 文件跳过, 共 %d 文件",
            imported, skipped, total_files,
        )
        return imported, skipped, total_files

    def _import_md_file(self, filepath: str) -> Tuple[bool, int]:
        """导入单个 .md 文件中的记忆

        解析策略：
        - 按空行分割段落
        - 跳过标题行（# 开头）、空行、URL 行
        - 每段落分类后插入
        """
        from tagger import classify, extract_tags

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        # 按块分割（空行分隔）
        blocks = re.split(r"\n\s*\n", text)
        entries: List[MemoryEntry] = []
        source_name = os.path.basename(filepath)

        for block in blocks:
            block = block.strip()
            # 跳过标题、空行、短片段
            if not block or len(block) < 10:
                continue
            if block.startswith("#"):
                continue

            tags = extract_tags(block)
            layer, _, _ = classify(block)

            entry = MemoryEntry(
                content=block[:500],  # 截断超长内容
                tags=tags,
                layer=layer,
                created_at=datetime.now(timezone.utc),
            )
            entries.append(entry)

        if entries:
            count = self.bulk_insert(entries, source=source_name)
            return True, count

        return True, 0

    # ── 内部方法 ────────────────────────────────────────────

    @staticmethod
    def _lambda_to_layers(lambda_value: float) -> List[str]:
        """λ 值到层级的映射"""
        if lambda_value <= 0.3:
            return ["constraint"]
        elif lambda_value <= 0.7:
            return ["constraint", "preference", "decision"]
        else:
            return ["constraint", "preference", "style", "decision", "pattern"]

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> MemoryEntry:
        """SQLite 行 → MemoryEntry"""
        import json
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


# 需要 import re，用于 _import_md_file
import re
