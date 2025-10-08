from __future__ import annotations

import os
import uuid
import time
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("portal.backend")

# ------------------------------------------------------------------------------
# Env / Config
# ------------------------------------------------------------------------------
FRONTEND_ORIGIN = os.getenv("PORTAL_BASE_URL", "http://localhost:3000")

# Default “system” user (no auth)
DEFAULT_USER_SUB = os.getenv("DEFAULT_USER_SUB", "system")
DEFAULT_USER_NAME = os.getenv("DEFAULT_USER_NAME", "Portal User")
DEFAULT_USER_EMAIL = os.getenv("DEFAULT_USER_EMAIL", "portal@example.com")

# Optional org id (only for display/target metadata)
LINKEDIN_ORG_ID = os.getenv("LINKEDIN_ORG_ID")

# test_complete_system hook
TEST_IMPORT_PATH = os.getenv("TEST_IMPORT_PATH", "tests.test_complete_system")
TEST_FUNCTION_NAME = os.getenv("TEST_FUNCTION_NAME", "test_complete_system")

# ------------------------------------------------------------------------------
# App & CORS
# ------------------------------------------------------------------------------
app = FastAPI(title="Content Portal API (no LinkedIn auth)", version="1.1.0")

# Easiest cross-origin behavior for Vercel previews: allow any origin by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("CORS_ALLOW_ANY", "1") == "1" else [FRONTEND_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

# ------------------------------------------------------------------------------
# In-memory DB (demo) aligned to your SQL model
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
        "user_id": None,  # demo: no DB FK
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
    Pull approved posts from typical shapes returned by test_complete_system:
      - batch.get_approved_posts() -> list[{content, hashtags?}]
      - dict keys: approved / approved_posts / posts -> list[...]
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
        if not isinstance(p, dict):
            continue
        content = (p.get("content") or p.get("text") or p.get("body") or "").strip()
        if not content:
            continue
        ht = p.get("hashtags") or p.get("tags") or []
        if isinstance(ht, str):
            ht = [ht]
        out.append({"content": content, "hashtags": _normalize_hashtags(ht)})
    return out

def _fallback_fake_batch() -> Any:
    """Fallback generator when openai (or the test module) is unavailable."""
    class FakeBatch:
        def __init__(self):
            self.id = uuid.uuid4().hex
            self._posts = [
                {"content": "We shipped a small UX polish today.", "hashtags": ["ProductUpdate", "UX"]},
                {"content": "3 quick lessons from our pipeline run.", "hashtags": ["Engineering", "DevNotes"]},
                {"content": "Roadmap peek: dashboard cleanup + copy-to-clipboard.", "hashtags": ["Startup", "SaaS"]},
            ]
        def get_approved_posts(self):
            return self._posts
    return FakeBatch()

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

# --- legacy alias so old UI doesn't 404 and cause re-renders -------------------
@app.get("/api/approved")
def api_approved_alias():
    # Return all stored posts (you can filter to QUEUED if you prefer)
    return list(sorted(DB["posts"].values(), key=lambda r: r["created_at"], reverse=True))

# --- posts (create + list) ----------------------------------------------------
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
    Store a post locally (no LinkedIn).
    'publish_now' just toggles lifecycle to PUBLISHED locally.
    """
    user = current_user()

    if payload.target == "ORG":
        if not payload.org_id and LINKEDIN_ORG_ID:
            payload.org_id = LINKEDIN_ORG_ID
        target_type = "ORG"
        target_urn = f"urn:li:organization:{payload.org_id or 'unknown'}"
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
    # Global queue
    return list(sorted(DB["posts"].values(), key=lambda r: r["created_at"], reverse=True))

# --- run the full system (generate approved posts) ----------------------------
@app.post("/api/run-batch")
def run_batch():
    """
    Attempt to run tests.test_complete_system.test_complete_system.
    If openai (or the test module) is missing, fall back to a built-in generator
    so the UI remains usable.
    """
    batch = None
    try:
        mod = __import__(TEST_IMPORT_PATH, fromlist=[TEST_FUNCTION_NAME])
        fn = getattr(mod, TEST_FUNCTION_NAME)
        # support sync/async
        if getattr(fn, "__code__", None) and (fn.__code__.co_flags & 0x80):
            import asyncio
            batch = asyncio.run(fn())
        else:
            batch = fn()
    except ModuleNotFoundError as e:
        # Typical case: openai not installed or test module missing.
        logger.error("Module import error, using fallback generator: %s", e)
        batch = _fallback_fake_batch()
    except Exception as e:
        logger.error("Test run error, using fallback generator: %s", e, exc_info=True)
        batch = _fallback_fake_batch()

    approved = _extract_posts_from_batch(batch)
    logger.info("Approved from system run: %d", len(approved))

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

# --- utility ------------------------------------------------------------------
@app.post("/api/approved/clear")
def clear_all():
    n = len(DB["posts"])
    DB["posts"].clear()
    return {"deleted": n}

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
