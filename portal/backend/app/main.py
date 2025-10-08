# portal/backend/app/main.py
import os
import json
import time
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# --------------------------------------------------------------------------------------
# Env / Config
# --------------------------------------------------------------------------------------
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "http://localhost:3000")

# CORS: comma-separated list of origins, or "*" (default)
_cors = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if o.strip()]
ALLOW_ALL = _cors == ["*"]

# --------------------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------------------
app = FastAPI(title="Content Portal API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ALLOW_ALL else _cors,
    allow_credentials=False,  # no cookie/session auth in this simplified portal
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------------------
# In-memory global queue (shared by everyone)
# Shape matches FE expectations for "approved" items
# --------------------------------------------------------------------------------------
APPROVED_QUEUE: List[Dict[str, Any]] = []


def _approved_from_batch(batch) -> List[Dict[str, Any]]:
    """
    Convert the batch's approved posts to the FE 'approved' shape.
    """
    items: List[Dict[str, Any]] = []
    if not batch or not getattr(batch, "get_approved_posts", None):
        return items

    for post in batch.get_approved_posts():
        # Each 'post' is your domain object; adapt as needed
        content = getattr(post, "content", "") or ""
        hashtags = getattr(post, "hashtags", None) or []
        items.append(
            {
                "id": uuid.uuid4().hex,
                "content": content,
                "hashtags": hashtags,
                "status": "approved",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "li_post_id": None,
                "error_message": None,
            }
        )
    return items


# --------------------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Content Portal API",
        "portal_base_url": PORTAL_BASE_URL,
        "cors_allow_origins": _cors,
    }


@app.get("/healthz")
def healthz():
    return {"ok": True, "time": int(time.time())}


@app.get("/api/approved")
def get_approved():
    """
    Return whatever is currently in the global approved queue
    (copy-paste posts for the dashboard).
    """
    return APPROVED_QUEUE


@app.post("/api/approved/clear")
def clear_approved():
    """
    Clear the global queue.
    """
    deleted = len(APPROVED_QUEUE)
    APPROVED_QUEUE.clear()
    return {"deleted": deleted}


@app.post("/api/run-batch")
async def run_batch():
    """
    Run the full content pipeline (tests/test_complete_system.test_complete_system),
    using the REAL OpenAI client if OPENAI_API_KEY is present.

    We do NOT attempt to publish to LinkedIn here; we just fill the approved queue
    with human-copyable posts for the dashboard.
    """
    try:
        # Import here so the API process loads only when needed.
        from tests.test_complete_system import test_complete_system as run_full

        # Run your full system once; do not publish to LinkedIn from here
        batch = await run_full(run_publish=False)

        # Convert approved to FE shape and append to global queue
        newly_approved = _approved_from_batch(batch)
        APPROVED_QUEUE.extend(newly_approved)

        return {
            "ok": True,
            "batch_id": getattr(batch, "id", None),
            "approved_count": len(newly_approved),
            "total_in_queue": len(APPROVED_QUEUE),
        }
    except ModuleNotFoundError as e:
        # Helpful error when a required dep (e.g., openai, structlog) is missing
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Missing dependency: {e}. "
                          f"Make sure it's listed in your repo-root requirements.txt and redeploy."
            },
        )
    except Exception as e:
        # Generic failure path with a short message
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )
