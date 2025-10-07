# portal/backend/app/main.py
from __future__ import annotations

import os
import uuid
import time
import logging
import threading
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Publishing Portal API", version="3.1.0")

# CORS: allow localhost + your main Vercel + any *.vercel.app previews
explicit_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
explicit_origins = [o.strip() for o in explicit_origins_env.split(",") if o.strip()]
if not explicit_origins:
    explicit_origins = [
        "http://localhost:3000",
        "https://content-validation-system.vercel.app",
    ]
allow_origin_regex = r"^https:\/\/([a-z0-9-]+\.)*vercel\.app$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=explicit_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=False,  # no sessions/cookies
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

# ------------------ Global approved queue (shared by everyone) -----------------
APPROVED_GLOBAL: List[Dict[str, Any]] = []
QUEUE_LOCK = threading.Lock()

class PublishIn(BaseModel):
    ids: List[str]
    target: str  # kept for UI compatibility ("MEMBER" | "ORG")
    publish_now: bool = True
    org_id: Optional[str] = None  # ignored here

class AddApprovedIn(BaseModel):
    content: str
    hashtags: Optional[List[str]] = None

@app.get("/")
def root():
    return {"ok": True, "message": "Publishing API (global queue, no OAuth)"}

@app.get("/api/health")
def health():
    return {"ok": True, "time": int(time.time())}

@app.get("/api/config")
def api_config():
    return {
        "auth_required": False,
        "global_queue": True,
        "cors_allow_origins": explicit_origins,
        "cors_regex": allow_origin_regex,
    }

@app.options("/api/approved")
def options_approved():
    return JSONResponse({"ok": True})

@app.get("/api/approved")
def get_approved():
    with QUEUE_LOCK:
        return APPROVED_GLOBAL

@app.post("/api/approved/add")
def add_approved(payload: AddApprovedIn):
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rec = {
        "id": uuid.uuid4().hex,
        "content": payload.content,
        "hashtags": payload.hashtags or [],
        "status": "approved",
        "created_at": now,
        "li_post_id": None,
        "error_message": None,
    }
    with QUEUE_LOCK:
        APPROVED_GLOBAL.append(rec)
        total = len(APPROVED_GLOBAL)
    return {"ok": True, "id": rec["id"], "total": total}

@app.post("/api/approved/publish")
def post_publish(payload: PublishIn):
    if not payload.ids:
        raise HTTPException(status_code=400, detail="No posts selected")

    success = 0
    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    with QUEUE_LOCK:
        idset = set(payload.ids)
        for it in APPROVED_GLOBAL:
            if it.get("id") in idset:
                try:
                    it["status"] = "published" if payload.publish_now else "draft"
                    it["li_post_id"] = it.get("li_post_id") or f"local-{uuid.uuid4().hex[:12]}"
                    it["published_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    it["published_as"] = payload.target
                    results.append(
                        {"id": it["id"], "li_post_id": it["li_post_id"], "status": it["status"]}
                    )
                    success += 1
                except Exception as e:
                    it["error_message"] = f"Local publish failed: {e}"
                    errors.append({"id": it.get("id"), "error": it["error_message"]})

    resp: Dict[str, Any] = {
        "successful": success,
        "results": results,
        "total_requested": len(payload.ids),
    }
    if errors:
        resp["errors"] = errors
    return resp

@app.post("/api/approved/clear")
def post_clear():
    with QUEUE_LOCK:
        deleted = len(APPROVED_GLOBAL)
        APPROVED_GLOBAL.clear()
    return {"deleted": deleted}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal error"})
