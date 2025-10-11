# portal/backend/app/main.py
"""
Complete Content Portal API with Prompt Management
Updated to include all routes and functionality
"""

import os
import sys
import json
import time
import uuid
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# --------------------------------------------------------------------------------------
# CRITICAL: Add project root to Python path so we can import from 'src'
# --------------------------------------------------------------------------------------
# Get the project root (three levels up from this file)
# portal/backend/app/main.py -> portal/backend -> portal -> PROJECT_ROOT
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print(f"🔧 Added to Python path: {PROJECT_ROOT}")

# --------------------------------------------------------------------------------------
# Now we can import FastAPI and other dependencies
# --------------------------------------------------------------------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import the prompts router (this will now work because PROJECT_ROOT is in sys.path)
from app.prompts_routes import router as prompts_router

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
# Register the prompts router
# --------------------------------------------------------------------------------------
app.include_router(prompts_router)

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
        "project_root": str(PROJECT_ROOT),
        "features": {
            "content_generation": True,
            "prompt_management": True,
            "batch_processing": True
        }
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


# --------------------------------------------------------------------------------------
# Additional Routes for Portal Features (Optional)
# --------------------------------------------------------------------------------------

@app.get("/api/me")
async def get_me():
    """
    Placeholder for user info endpoint
    Returns mock user data for now
    """
    return {
        "name": "Content Manager",
        "sub": "user_001",
        "email": "manager@jesseaeisembalm.com"
    }


@app.get("/api/orgs")
async def get_orgs():
    """
    Placeholder for organizations endpoint
    Returns empty list for now
    """
    return {
        "orgs": []
    }


@app.get("/api/posts")
async def get_posts():
    """
    Return all posts from the approved queue
    This is the same as /api/approved but with a different endpoint name
    for consistency with the frontend expectations
    """
    return APPROVED_QUEUE


@app.post("/api/posts")
async def create_post(payload: Dict[str, Any]):
    """
    Create a new post manually (not from batch generation)
    This allows users to add custom posts to the queue
    """
    try:
        commentary = payload.get("commentary", "")
        hashtags = payload.get("hashtags", [])
        target = payload.get("target", "AUTO")
        org_id = payload.get("org_id")
        
        if not commentary:
            return JSONResponse(
                status_code=400,
                content={"detail": "Commentary is required"}
            )
        
        # Create new post entry
        new_post = {
            "id": uuid.uuid4().hex,
            "target_type": target if target != "AUTO" else "MEMBER",
            "lifecycle": "draft",
            "commentary": commentary,
            "hashtags": hashtags,
            "li_post_id": None,
            "error_message": None,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        APPROVED_QUEUE.append(new_post)
        
        return {
            "ok": True,
            "post": new_post,
            "lifecycle": "draft"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )


# --------------------------------------------------------------------------------------
# Startup Event
# --------------------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """
    Run on application startup
    """
    print("="*60)
    print("🚀 Content Portal API Starting Up")
    print("="*60)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Portal Base URL: {PORTAL_BASE_URL}")
    print(f"CORS Origins: {_cors}")
    print(f"Features:")
    print(f"  - Content Generation: ✅")
    print(f"  - Prompt Management: ✅")
    print(f"  - Batch Processing: ✅")
    print("="*60)
    
    # Ensure config directory exists at project root
    config_dir = PROJECT_ROOT / "config"
    config_dir.mkdir(exist_ok=True)
    
    # Initialize prompts file if it doesn't exist
    prompts_file = config_dir / "prompts.json"
    if not prompts_file.exists():
        with open(prompts_file, 'w') as f:
            json.dump({}, f)
        print(f"✅ Created {prompts_file}")
    else:
        print(f"✅ Found existing {prompts_file}")


# --------------------------------------------------------------------------------------
# Main entry point (for local development)
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )