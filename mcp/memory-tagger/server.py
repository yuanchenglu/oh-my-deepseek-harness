"""Memory Tagger MCP Server — FastAPI HTTP Server

基于 I-12 Memory 粒度控制概念，提供 4 个 REST API 端点：
1. POST /memory/tag      — 输入内容 → 返回层级标签
2. POST /memory/query     — 按标签/层级查询记忆
3. POST /memory/filter    — 按 λ 值过滤记忆
4. GET  /memory/lambda/{task_type} — 任务类型 → λ 建议 + 过滤后记忆

数据持久化：SQLite (~/.hermes/mcp/memory-tagger.db)
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from models import (
    ErrorResponse,
    FilterRequest,
    FilterResponse,
    ImportResponse,
    LambdaResponse,
    MemoryEntry,
    MemoryLayer,
    QueryRequest,
    QueryResponse,
    TagRequest,
    TagResponse,
)
from storage import MemoryStorage
from tagger import classify, detect_task_type, extract_tags

# ── 日志 ────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("memory-tagger")

# ── 配置加载 ────────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> dict:
    """加载 config.yaml"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning("config.yaml 未找到，使用默认配置")
        return {}
    except yaml.YAMLError as e:
        logger.warning("config.yaml 解析失败: %s，使用默认配置", e)
        return {}


config = load_config()

# ── 存储层初始化 ─────────────────────────────────────────────

storage_config = config.get("storage", {})
db_path = os.path.expanduser(storage_config.get("db_path", "~/.hermes/mcp/memory-tagger.db"))
storage = MemoryStorage(db_path=db_path)

# ── 启动时导入 Hermes Memory ────────────────────────────────

if storage_config.get("import_on_startup", True):
    memories_dir = os.path.expanduser(
        storage_config.get("hermes_memories_dir", "~/.hermes/memories/")
    )
    imported, skipped, total = storage.import_from_hermes(memories_dir)
    logger.info("启动导入: %d 插入, %d 跳过, 共 %d 文件", imported, skipped, total)

# ── 任务类型 → λ 映射 ──────────────────────────────────────

TASK_LAMBDA_MAP: Dict[str, dict] = {}
task_mappings = config.get("task_type_mappings", {})
for task_type, mapping in task_mappings.items():
    if isinstance(mapping, dict):
        TASK_LAMBDA_MAP[task_type] = mapping

LAMBDA_LEVELS: List[dict] = config.get("lambda_mappings", {}).get("levels", [])
DEFAULT_LAMBDA = config.get("default_lambda", 0.5)
DEFAULT_LAMBDA_LABEL = config.get("default_lambda_label", "mixed")

# ── FastAPI 应用 ────────────────────────────────────────────

app = FastAPI(
    title="Memory Tagger MCP Server",
    description="Memory 标签分类 + λ 过滤中间层",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== API 端点 ==========


@app.post(
    "/memory/tag",
    response_model=TagResponse,
    responses={422: {"model": ErrorResponse}},
    summary="输入内容 → 返回层级标签",
    description="对单条记忆内容进行层级分类，输出标签、层级和置信度",
)
async def tag_memory(req: TagRequest):
    """POST /memory/tag — 输入内容 → 返回层级标签"""
    try:
        layer, matched_kws, confidence = classify(req.content)
        tags = extract_tags(req.content)

        return TagResponse(
            content=req.content,
            tags=tags,
            layer=layer,
            confidence=confidence,
        )
    except Exception as e:
        logger.error("tag_memory 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/memory/query",
    response_model=QueryResponse,
    responses={422: {"model": ErrorResponse}},
    summary="按标签/层级查询记忆",
    description="从持久化存储中按标签和/或层级检索记忆条目",
)
async def query_memory(req: QueryRequest):
    """POST /memory/query — 按标签/层级查询记忆"""
    try:
        entries = storage.query(
            tags=req.tags,
            layer=req.layer,
            limit=req.limit,
        )
        return QueryResponse(entries=entries, total=len(entries))
    except Exception as e:
        logger.error("query_memory 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/memory/filter",
    response_model=FilterResponse,
    responses={422: {"model": ErrorResponse}},
    summary="按 λ 值过滤记忆",
    description=(
        "λ ∈ [0, 1]：0.0=仅约束层, 0.5=约束+偏好+决策, 1.0=全部。"
        "支持从持久化存储过滤，并同时对新输入做即时分类。"
    ),
)
async def filter_memory(req: FilterRequest):
    """POST /memory/filter — 按 λ 值过滤记忆"""
    try:
        entries = storage.filter_by_lambda(req.lambda_value, limit=req.limit)
        layers = storage.get_layers_for_lambda(req.lambda_value)

        return FilterResponse(
            entries=entries,
            total=len(entries),
            lambda_value=req.lambda_value,
            included_layers=layers,
        )
    except Exception as e:
        logger.error("filter_memory 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/memory/lambda/{task_type}",
    response_model=LambdaResponse,
    responses={422: {"model": ErrorResponse}},
    summary="任务类型 → 建议 λ + 过滤后记忆",
    description=(
        "根据任务类型（convergent / divergent / mixed）返回建议的 λ 值"
        "以及对应的过滤后记忆列表。"
    ),
)
async def get_lambda_for_task(
    task_type: str,
    limit: int = Query(default=50, ge=1, le=500, description="返回条数上限"),
):
    """GET /memory/lambda/{task_type} — 任务类型 → λ 建议"""
    valid_types = {"convergent", "divergent", "mixed"}

    if task_type not in valid_types:
        logger.warning("未知任务类型: %s，使用默认 λ=%s", task_type, DEFAULT_LAMBDA)
        suggested_lambda = DEFAULT_LAMBDA
        label = DEFAULT_LAMBDA_LABEL
    else:
        mapping = TASK_LAMBDA_MAP.get(task_type, {})
        suggested_lambda = mapping.get("suggested_lambda", DEFAULT_LAMBDA)
        label = mapping.get("label", DEFAULT_LAMBDA_LABEL)

    entries = storage.filter_by_lambda(suggested_lambda, limit=limit)

    return LambdaResponse(
        task_type=task_type,
        suggested_lambda=suggested_lambda,
        label=label,
        entries=entries,
        total=len(entries),
    )


@app.get(
    "/health",
    summary="健康检查",
    description="返回服务状态和存储统计",
)
async def health_check():
    """GET /health — 健康检查"""
    counts = storage.count_by_layer()
    return {
        "status": "ok",
        "total_memories": storage.count_total(),
        "layers": counts,
        "db_path": storage.db_path,
    }


@app.get(
    "/memory/import",
    response_model=ImportResponse,
    summary="重新导入 Hermes Memory",
    description="手动触发从 Hermes Memory 目录重新导入初始化数据",
)
async def import_memories():
    """GET /memory/import — 重新导入 Hermes Memory"""
    memories_dir = os.path.expanduser(
        storage_config.get("hermes_memories_dir", "~/.hermes/memories/")
    )
    imported, skipped, total = storage.import_from_hermes(memories_dir)
    return ImportResponse(imported=imported, skipped=skipped, total_files=total)


# ── 入口 ────────────────────────────────────────────────────


def main():
    """启动 FastAPI 服务"""
    import uvicorn

    host = os.environ.get("MEMORY_TAGGER_HOST", "127.0.0.1")
    port = int(os.environ.get("MEMORY_TAGGER_PORT", "8100"))

    logger.info("启动 Memory Tagger MCP Server — %s:%d", host, port)
    logger.info("数据库路径: %s", storage.db_path)

    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
