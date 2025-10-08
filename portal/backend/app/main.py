from __future__ import annotations

import os
import sys
import uuid
import time
import logging
import asyncio
import importlib.util
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Make sure project root is importable (for tests/ and src/)
sys.path.insert(0, os.path.abspath("."))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("portal.backend")

# ------------------------------------------------------------------------------
# Env / Config
# ------------------------------------------------------------------------------
FRONTEND_ORIGIN = os.getenv("PORTAL_BASE_URL", "http://localhost:3000")

# Single global user (no LinkedIn auth)
DEFAULT_USER_SUB = os.getenv("DEFAULT_USER_SUB", "system")
DEFAULT_USER_NAME = os.getenv("DEFAULT_USER_NAME", "Portal User")
DEFAULT_USER_EMAIL = os.getenv("DEFAULT_USER_EMAIL", "portal@example.com")

# Optional org id for display/target metadata only
LINKEDIN_ORG_ID = os.getenv("LINKEDIN_ORG_ID")

# Test runner path
TEST_IMPORT_PATH = os.getenv("TEST_IMPORT_PATH", "tests.test_complete_system")
TEST_FUNCTION_NAME = os.getenv("TEST_FUNCTION_NAME", "test_complete_system")

# ------------------------------------------------------------------------------
# App & CORS
# ------------------------------------------------------------------------------
app = FastAPI(title="Content Portal API (real OpenAI required)", version="1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("CORS_ALLOW_ANY", "1") == "1" else [FRONTEND_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

# ------------------------------------------------------------------------------
# In-memory DB (demo) aligned with your SQL model
# ------------------------------------------------------------------------------
DB: Dict[str, Dict[str, Any]] = {
    "users": {},   # li_sub -> {sub, name, email, created_at}
    "posts": {},   # id -> post row
}

def _ensure_default_user():
    if DEFAULT_USER_SUB not in DB["users"]:
        DB["users"][DEFAULT_USER_SUB] = {
            "sub": DEFAULT_USER_SUB,
            "name": DEFAULT_USER_NAME,
            "email": DEFAULT_USER_EMAIL,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

_ensure_default_user()

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

def current_user() -> Dict[str, Any]:
    # No auth: always the default user
    return DB["users"][DEFAULT_USER_SUB]

def _normalize_hashtags(hashtags: Optional[List[str]]) -> List[str]:
    out: List[str] = []
    for h in (hashtags or []):
        s = str(h).strip().lstrip("#")
        if s:
            out.append(s)
    return out

def _new_post_row(
    commentary: str,
    hashtags: List[str],
    target_type: str,
    target_urn: str,
    lifecycle: str = "QUEUED",
    li_post_id: Optional[str] = None,
    error_message: Optional[str] = None,
    scheduled_at: Optional[str] = None,
    published_at: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "id": uuid.uuid4().hex,
        "user_id": None,  # demo only
        "user_sub": DEFAULT_USER_SUB,
        "target_type": target_type,     # 'MEMBER' | 'ORG'
        "target_urn": target_urn,       # urn:li:person:SUB or urn:li:organization:ID
        "commentary": commentary,
        "hashtags": hashtags,
        "lifecycle": lifecycle,         # QUEUED | PROCESSING | PUBLISHED | FAILED
        "li_post_id": li_post_id,
        "error_message": error_message,
        "scheduled_at": scheduled_at,
        "created_at": now_iso(),
        "published_at": published_at,
    }

def _extract_posts_from_batch(batch: Any) -> List[Dict[str, Any]]:
    """
    Pull approved posts from typical shapes returned by tests/test_complete_system:
      - batch.get_approved_posts() -> list of objects or dicts
      - dict keys: approved / approved_posts / posts -> list[...]
    Each item should yield {content, hashtags?}.
    """
    posts = None
    if hasattr(batch, "get_approved_posts"):
        try:
            posts = batch.get_approved_posts()
        except Exception:
            posts = None
    if posts is None and isinstance(batch, dict):
        for key in ("approved", "approved_posts", "posts"):
            if key in batch and isinstance(batch[key], list):
                posts = batch[key]
                break
    if not posts:
        return []

    out: List[Dict[str, Any]] = []
    for p in posts:
        if isinstance(p, dict):
            content = (p.get("content") or p.get("text") or p.get("body") or "").strip()
            ht = p.get("hashtags") or p.get("tags") or []
        else:
            content = (getattr(p, "content", None) or getattr(p, "text", None) or "").strip()
            ht = getattr(p, "hashtags", []) or getattr(p, "tags", []) or []
        if not content:
            continue
        if isinstance(ht, str):
            ht = [ht]
        out.append({"content": content, "hashtags": _normalize_hashtags(ht)})
    return out

def _openai_installed() -> bool:
    return importlib.util.find_spec("openai") is not None

async def _run_test_function_async() -> Any:
    """
    Import and run tests.test_complete_system.test_complete_system(run_publish=False).
    Returns whatever the test returns (batch-like object).
    """
    # Enforce REAL OpenAI if the key is present
    if os.getenv("OPENAI_API_KEY") and not _openai_installed():
        raise RuntimeError(
            "OPENAI_API_KEY is set, but the 'openai' package is not installed. "
            "Add 'openai>=1.7,<2' to requirements.txt and redeploy."
        )

    # Import module dynamically
    mod = __import__(TEST_IMPORT_PATH, fromlist=[TEST_FUNCTION_NAME])
    fn = getattr(mod, TEST_FUNCTION_NAME, None)
    if fn is None:
        raise RuntimeError(f"Function {TEST_FUNCTION_NAME} not found in {TEST_IMPORT_PATH}")

    # Call with run_publish=False so no LinkedIn calls happen
    result = fn(run_publish=False)
    if asyncio.iscoroutine(result):
        result = await result
    return result

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"ok": True, "time": int(time.time()), "posts": len(DB["posts"])}

@app.get("/api/me")
def api_me():
    u = current_user()
    return {"sub": u["sub"], "name": u["name"], "email": u.get("email"), "org_preferred": LINKEDIN_ORG_ID}

@app.get("/api/orgs")
def api_orgs():
    # If env has org id, return it; else empty list.
    if LINKEDIN_ORG_ID:
        return {"orgs": [{"id": LINKEDIN_ORG_ID, "urn": f"urn:li:organization:{LINKEDIN_ORG_ID}"}]}
    return {"orgs": []}

# Legacy alias so old callers don't 404
@app.get("/api/approved")
def api_approved_alias():
    return list(sorted(DB["posts"].values(), key=lambda r: r["created_at"], reverse=True))

from pydantic import BaseModel

class ComposeIn(BaseModel):
    commentary: str
    hashtags: List[str] = []
    target: Literal["AUTO", "MEMBER", "ORG"] = "AUTO"
    org_id: Optional[str] = None
    publish_now: bool = True

@app.post("/api/posts")
def create_post(payload: ComposeIn):
    """
    Store a post locally (copy/paste workflow). No LinkedIn calls.
    """
    user = current_user()

    if payload.target == "ORG":
        org_id = payload.org_id or LINKEDIN_ORG_ID or "unknown"
        target_type = "ORG"
        target_urn = f"urn:li:organization:{org_id}"
    elif payload.target == "MEMBER":
        target_type = "MEMBER"
        target_urn = f"urn:li:person:{user['sub']}"
    else:
        if LINKEDIN_ORG_ID:
            target_type = "ORG"
            target_urn = f"urn:li:organization:{LINKEDIN_ORG_ID}"
        else:
            target_type = "MEMBER"
            target_urn = f"urn:li:person:{user['sub']}"

    row = _new_post_row(
        commentary=payload.commentary,
        hashtags=_normalize_hashtags(payload.hashtags),
        target_type=target_type,
        target_urn=target_urn,
        lifecycle="PUBLISHED" if payload.publish_now else "QUEUED",
        li_post_id=None,
    )
    DB["posts"][row["id"]] = row
    return row

@app.get("/api/posts")
def list_posts():
    # Global queue (all users)
    return list(sorted(DB["posts"].values(), key=lambda r: r["created_at"], reverse=True))

@app.post("/api/run-batch")
async def run_batch():
    """
    Run the full system test and ingest approved posts into the local queue.
    Always uses run_publish=False (no LinkedIn).
    Requires real OpenAI when OPENAI_API_KEY is set.
    """
    try:
        batch = await _run_test_function_async()
        approved = _extract_posts_from_batch(batch)
        logger.info("Approved posts from test: %d", len(approved))

        user = current_user()
        target_type = "ORG" if LINKEDIN_ORG_ID else "MEMBER"
        target_urn = f"urn:li:organization:{LINKEDIN_ORG_ID}" if LINKEDIN_ORG_ID else f"urn:li:person:{user['sub']}"

        added = 0
        for p in approved:
            row = _new_post_row(
                commentary=p["content"],
                hashtags=_normalize_hashtags(p.get("hashtags") or []),
                target_type=target_type,
                target_urn=target_urn,
                lifecycle="QUEUED",
            )
            DB["posts"][row["id"]] = row
            added += 1

        return {
            "batch_id": getattr(batch, "id", None),
            "approved": len(approved),
            "added": added,
            "published": 0,
            "errors": [],
        }
    except Exception as e:
        logger.error("Run-batch error: %s", e, exc_info=True)
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.post("/api/approved/clear")
def clear_all():
    n = len(DB["posts"])
    DB["posts"].clear()
    return {"deleted": n}
