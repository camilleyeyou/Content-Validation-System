import os
import json
import time
import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ---------------------------
# Simple, durable storage (SQLite)
# ---------------------------
from sqlalchemy import (
    create_engine, MetaData, Table, Column, String, Text, DateTime
)
from sqlalchemy.sql import select, insert, delete
from sqlalchemy.engine import Engine, Row

# ===========================
# Env / basic config
# ===========================
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "http://localhost:3000")
PORT = int(os.getenv("PORT", "8080"))

# ---- CORS config ----
# Prefer explicit list via CORS_ALLOW_ORIGINS (comma-separated).
# Otherwise fall back to a permissive regex that matches vercel/railway/localhost.
def _split_env_list(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]

CORS_ALLOW_ORIGINS = _split_env_list(os.getenv("CORS_ALLOW_ORIGINS"))
CORS_ALLOW_ORIGIN_REGEX = os.getenv(
    "CORS_ALLOW_ORIGIN_REGEX",
    # vercel/railway/localhost (http or https)
    r"^https?:\/\/([a-z0-9-]+\.)*(vercel\.app|railway\.app|localhost(:\d{1,5})?)$"
)

# Path for SQLite file
DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(DATA_DIR, 'app.db')}")

# ===========================
# DB setup (SQLAlchemy Core)
# ===========================
engine: Engine = create_engine(DB_URL, future=True)
meta = MetaData()

# A single global queue of generated posts
posts = Table(
    "posts",
    meta,
    Column("id", String, primary_key=True),
    Column("content", Text, nullable=False),
    Column("hashtags", Text, nullable=True),        # JSON-encoded array
    Column("status", String, nullable=False),       # 'approved' | 'published' | 'failed' | 'draft'
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("li_post_id", String, nullable=True),
    Column("error_message", Text, nullable=True),
)

def init_db():
    meta.create_all(engine)

def row_to_approved(rec: Row) -> Dict[str, Any]:
    return {
        "id": rec["id"],
        "content": rec["content"],
        "hashtags": json.loads(rec["hashtags"] or "[]"),
        "status": rec["status"],
        "created_at": rec["created_at"].isoformat(),
        "li_post_id": rec["li_post_id"],
        "error_message": rec["error_message"],
    }

# ===========================
# App
# ===========================
app = FastAPI(title="Content Portal API", version="1.2.1")

# IMPORTANT: allow_origin_regex supports changing Vercel preview URLs.
# We also keep allow_origins if you set CORS_ALLOW_ORIGINS explicitly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS if CORS_ALLOW_ORIGINS else [],
    allow_origin_regex=CORS_ALLOW_ORIGIN_REGEX if not CORS_ALLOW_ORIGINS else None,
    allow_credentials=True,   # ok even if we don't use cookies; FE may send credentials
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# ===========================
# Models / Schemas
# ===========================
class PublishIn(BaseModel):
    ids: List[str]
    target: str  # MEMBER | ORG (kept for compatibility; currently not used for API posting)
    publish_now: bool = True
    org_id: Optional[str] = None

# ===========================
# Helpers
# ===========================
def now_utc() -> datetime:
    return datetime.now(timezone.utc)

# -----------------------------------------------------------
# SYSTEM PIPELINE: call your real test_complete_system runner
# -----------------------------------------------------------
from tests.test_complete_system import test_complete_system  # your actual full pipeline

async def run_pipeline_and_collect() -> Dict[str, Any]:
    """
    Runs the full generation/validation pipeline and writes APPROVED posts to SQLite.
    Returns a summary dict: {approved_count, total_in_queue, batch_id}
    """
    batch = await test_complete_system(run_publish=False)

    approved_posts = getattr(batch, "get_approved_posts", lambda: [])()
    approved_count = 0

    with engine.begin() as conn:
        for p in approved_posts:
            content = getattr(p, "content", "") or ""
            hashtags = getattr(p, "hashtags", None) or []

            rec = {
                "id": uuid.uuid4().hex,
                "content": content,
                "hashtags": json.dumps(hashtags),
                "status": "approved",
                "created_at": now_utc(),
                "li_post_id": None,
                "error_message": None,
            }
            conn.execute(insert(posts).values(**rec))
            approved_count += 1

        total_in_queue = conn.execute(select(posts.c.id)).fetchall()
        total_in_queue = len(total_in_queue)

    return {
        "approved_count": approved_count,
        "batch_id": getattr(batch, "id", None),
        "total_in_queue": total_in_queue,
    }

# ===========================
# Routes
# ===========================
@app.get("/api/health")
def health():
    return {"ok": True, "time": int(time.time())}

@app.get("/api/approved")
def get_approved():
    """Return the full global queue, newest first."""
    with engine.begin() as conn:
        rows = conn.execute(
            select(posts).order_by(posts.c.created_at.desc())
        ).fetchall()
    return [row_to_approved(r) for r in rows]

@app.post("/api/approved/clear")
def clear_approved():
    with engine.begin() as conn:
        n = conn.execute(select(posts.c.id)).fetchall()
        conn.execute(delete(posts))
    return {"deleted": len(n)}

@app.post("/api/approved/publish")
def mark_published(payload: PublishIn):
    """
    For now, just mark items as 'published' locally.
    (We are not posting to LinkedIn per your simpler flow.)
    """
    if not payload.ids:
        raise HTTPException(status_code=400, detail="No posts selected")
    updated = 0
    with engine.begin() as conn:
        existing = conn.execute(
            select(posts).where(posts.c.id.in_(payload.ids))
        ).fetchall()

        for r in existing:
            conn.execute(
                posts.update()
                .where(posts.c.id == r["id"])
                .values(status="published")
            )
            updated += 1

    return {"successful": updated, "results": [{"id": i, "status": "published"} for i in payload.ids]}

@app.post("/api/run-batch")
async def run_batch_route():
    """
    Run your full pipeline and store APPROVED posts in SQLite.
    """
    try:
        result = await run_pipeline_and_collect()
        return {
            "approved_count": result["approved_count"],
            "batch_id": result["batch_id"],
            "total_in_queue": result["total_in_queue"],
        }
    except ModuleNotFoundError as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Missing dependency: {e}. Make sure it's listed in your repo-root requirements.txt and redeploy."},
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Content Portal API (SQLite-backed queue)",
        "db": DB_URL,
        "portal_base_url": PORTAL_BASE_URL,
        "cors_allow_origins": CORS_ALLOW_ORIGINS,
        "cors_allow_origin_regex": CORS_ALLOW_ORIGIN_REGEX if not CORS_ALLOW_ORIGINS else None,
    }
