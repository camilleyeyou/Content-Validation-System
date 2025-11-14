# portal/backend/app/main.py
"""
Complete Content Portal API with Prompt Management, Image Support, and Wizard
Fixed for both local development and deployment
NOW WITH: Guided wizard for single-post creation
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
# CRITICAL: Setup paths for both development and deployment
# --------------------------------------------------------------------------------------
# Get current file location
CURRENT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = CURRENT_DIR.parent.resolve()
PORTAL_DIR = BACKEND_DIR.parent.resolve()
PROJECT_ROOT = PORTAL_DIR.parent.resolve()

# Add both backend and project root to path
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print(f"🔧 Backend dir: {BACKEND_DIR}")
print(f"🔧 Project root: {PROJECT_ROOT}")

# --------------------------------------------------------------------------------------
# Now we can import FastAPI and other dependencies
# --------------------------------------------------------------------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Import routers using relative import
from .prompts_routes import router as prompts_router
from .wizard_routes import router as wizard_router
from .cost_routes import router as cost_router  # COST TRACKING


# --------------------------------------------------------------------------------------
# Env / Config
# --------------------------------------------------------------------------------------
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "http://localhost:3000")

# If your backend is behind a different origin than the frontend, set BACKEND_BASE_URL
# e.g., https://api.content-validation-system.yourdomain.com
BACKEND_BASE_URL = (os.getenv("BACKEND_BASE_URL") or "").rstrip("/")

# Where images are stored on disk (where the image agent saves files)
# Convert to absolute path based on PROJECT_ROOT to avoid working directory issues
IMAGE_DIR_RAW = os.getenv("IMAGE_DIR", "data/images")
if Path(IMAGE_DIR_RAW).is_absolute():
    IMAGE_DIR = IMAGE_DIR_RAW
else:
    IMAGE_DIR = str(PROJECT_ROOT / IMAGE_DIR_RAW)
    
print(f"🔧 Images directory: {IMAGE_DIR}")

# Public route where images are served (mounted below)
IMAGES_ROUTE = os.getenv("IMAGES_ROUTE", "/images").rstrip("/") or "/images"

# Base URL the FE should use for images:
# If BACKEND_BASE_URL is set -> {BACKEND_BASE_URL}{IMAGES_ROUTE}
# Else -> just IMAGES_ROUTE (relative; assumes FE proxies to backend)
PUBLIC_IMAGES_BASE = f"{BACKEND_BASE_URL}{IMAGES_ROUTE}" if BACKEND_BASE_URL else IMAGES_ROUTE

# CORS: comma-separated list of origins, or "*" (default)
_cors = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if o.strip()]
ALLOW_ALL = _cors == ["*"]

# --------------------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------------------
app = FastAPI(title="Content Portal API with Wizard", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ALLOW_ALL else _cors,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static images (serve files from IMAGE_DIR at IMAGES_ROUTE)
# e.g., GET https://<backend>/images/<filename>.png
Path(IMAGE_DIR).mkdir(parents=True, exist_ok=True)
app.mount(IMAGES_ROUTE, StaticFiles(directory=IMAGE_DIR), name="images")

# --------------------------------------------------------------------------------------
# Register routers
# --------------------------------------------------------------------------------------
app.include_router(prompts_router)
app.include_router(wizard_router, prefix="/api/wizard", tags=["wizard"])  # FIXED: Added prefix!
app.include_router(cost_router)  # COST TRACKING


# --------------------------------------------------------------------------------------
# In-memory global queue
# --------------------------------------------------------------------------------------
APPROVED_QUEUE: List[Dict[str, Any]] = []


def _images_base() -> str:
    """Return the base URL (absolute or relative) for served images."""
    return PUBLIC_IMAGES_BASE  # already normalized above


def _to_public_image_url(maybe_path: Optional[str]) -> Optional[str]:
    """
    Convert various forms of stored image references into a browser-loadable URL.
    - If it's already an http(s) URL, return as-is.
    - If it starts with the mounted route (/images/...), return as-is.
    - If it's a local filesystem path like data/images/xyz.png, map to /images/xyz.png.
    - If it's just a filename, map to /images/<filename>.
    """
    if not maybe_path:
        return None

    val = str(maybe_path).strip()

    # Already absolute URL
    if val.startswith("http://") or val.startswith("https://"):
        return val

    # Already using the public images route
    if val.startswith(IMAGES_ROUTE + "/"):
        # Prepend backend base if configured, else keep relative
        if BACKEND_BASE_URL:
            return f"{BACKEND_BASE_URL}{val}"
        return val

    p = Path(val)

    # If it's a path under IMAGE_DIR (e.g., data/images/file.png), use filename
    try:
        # Resolve against current working dir safely
        if (IMAGE_DIR in val) or (Path(IMAGE_DIR).resolve() in Path(val).resolve().parents):
            filename = p.name
            base = _images_base().rstrip("/")
            return f"{base}/{filename}"
    except Exception:
        # If resolve() fails (nonexistent), fall through to filename mapping
        pass

    # If it's just a filename with an image extension, serve it under images route
    if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"} and p.name == val:
        base = _images_base().rstrip("/")
        return f"{base}/{p.name}"

    # Last resort: treat it as a filename
    base = _images_base().rstrip("/")
    return f"{base}/{p.name}"


def _approved_from_batch(batch) -> List[Dict[str, Any]]:
    """Convert the batch's approved posts to the FE 'approved' shape with images."""
    items: List[Dict[str, Any]] = []
    if not batch or not getattr(batch, "get_approved_posts", None):
        return items

    for post in batch.get_approved_posts():
        content = getattr(post, "content", "") or ""
        hashtags = getattr(post, "hashtags", None) or []

        # Extract possible image data from the post
        raw_image_url = getattr(post, "image_url", None)  # may be a filesystem path or a public URL
        image_description = getattr(post, "image_description", None)
        image_prompt = getattr(post, "image_prompt", None)
        image_revised_prompt = getattr(post, "image_revised_prompt", None)

        # Normalize the image URL so FE can render it (map local paths -> served URLs)
        public_image_url = _to_public_image_url(raw_image_url)

        items.append(
            {
                "id": uuid.uuid4().hex,
                "content": content,
                "hashtags": hashtags,
                # Image fields (Google Gemini generated)
                "image_url": public_image_url,
                "image_description": image_description,
                "image_prompt": image_prompt,
                "image_revised_prompt": image_revised_prompt,
                "has_image": public_image_url is not None,
                # Status fields
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
        "message": "Content Portal API with Google Gemini Image Generation + Wizard",
        "portal_base_url": PORTAL_BASE_URL,
        "backend_base_url": BACKEND_BASE_URL or "(relative)",
        "images_route": IMAGES_ROUTE,
        "public_images_base": _images_base(),
        "cors_allow_origins": _cors,
        "project_root": str(PROJECT_ROOT),
        "features": {
            "content_generation": True,
            "image_generation": True,
            "image_provider": "google_gemini_2.5_flash",
            "prompt_management": True,
            "batch_processing": True,
            "wizard_mode": True  # NEW
        }
    }


@app.get("/healthz")
def healthz():
    return {"ok": True, "time": int(time.time())}


@app.get("/api/debug/images")
def debug_images():
    """Debug endpoint to check image directory and list files"""
    import os
    from pathlib import Path
    
    image_path = Path(IMAGE_DIR)
    
    return {
        "image_dir": IMAGE_DIR,
        "image_dir_exists": image_path.exists(),
        "image_dir_is_dir": image_path.is_dir(),
        "images_route": IMAGES_ROUTE,
        "public_images_base": PUBLIC_IMAGES_BASE,
        "cwd": os.getcwd(),
        "files": [f.name for f in image_path.glob("*.png")] if image_path.exists() else [],
        "file_count": len(list(image_path.glob("*.png"))) if image_path.exists() else 0
    }


@app.get("/api/approved")
def get_approved():
    """Return whatever is currently in the global approved queue"""
    return APPROVED_QUEUE


@app.post("/api/approved/clear")
def clear_approved():
    """Clear the global queue."""
    deleted = len(APPROVED_QUEUE)
    APPROVED_QUEUE.clear()
    return {"deleted": deleted}


@app.post("/api/run-batch")
async def run_batch():
    """Run the full content pipeline with Google Gemini image generation"""
    try:
        from tests.test_complete_system import test_complete_system as run_full
        batch = await run_full(run_publish=False)
        newly_approved = _approved_from_batch(batch)
        APPROVED_QUEUE.extend(newly_approved)

        # Count posts with images
        posts_with_images = sum(1 for p in newly_approved if p.get("has_image"))

        return {
            "ok": True,
            "batch_id": getattr(batch, "id", None),
            "approved_count": len(newly_approved),
            "posts_with_images": posts_with_images,
            "image_provider": "google_gemini",
            "total_in_queue": len(APPROVED_QUEUE),
        }
    except ModuleNotFoundError as e:
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Missing dependency: {e}. "
                          f"Make sure it's listed in your requirements.txt."
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )


@app.get("/api/me")
async def get_me():
    """Placeholder for user info endpoint"""
    return {
        "name": "Content Manager",
        "sub": "user_001",
        "email": "manager@jesseaeisembalm.com"
    }


@app.get("/api/orgs")
async def get_orgs():
    """Placeholder for organizations endpoint"""
    return {"orgs": []}


@app.get("/api/posts")
async def get_posts():
    """Return all posts from the approved queue"""
    return APPROVED_QUEUE


@app.post("/api/posts")
async def create_post(payload: Dict[str, Any]):
    """Create a new post manually (with optional image URL)"""
    try:
        commentary = payload.get("commentary", "")
        hashtags = payload.get("hashtags", [])
        target = payload.get("target", "AUTO")

        # Accept optional image data (can be from Gemini or manual upload)
        raw_image_url = payload.get("image_url")
        image_description = payload.get("image_description")

        if not commentary:
            return JSONResponse(
                status_code=400,
                content={"detail": "Commentary is required"}
            )

        # Normalize any provided image URL/path to a public URL
        public_image_url = _to_public_image_url(raw_image_url) if raw_image_url else None

        new_post = {
            "id": uuid.uuid4().hex,
            "target_type": target if target != "AUTO" else "MEMBER",
            "lifecycle": "draft",
            "commentary": commentary,
            "hashtags": hashtags,
            # Image fields (supports Gemini or manual uploads)
            "image_url": public_image_url,
            "image_description": image_description,
            "has_image": public_image_url is not None,
            # Status fields
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
    """Run on application startup"""
    print("="*60)
    print("🚀 Content Portal API Starting Up")
    print("="*60)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Portal Base URL: {PORTAL_BASE_URL}")
    print(f"Backend Base URL: {BACKEND_BASE_URL or '(relative)'}")
    print(f"Images Dir: {IMAGE_DIR}")
    print(f"Images Route: {IMAGES_ROUTE}")
    print(f"Public Images Base: {_images_base()}")
    print(f"CORS Origins: {_cors}")
    print(f"Features:")
    print(f"  - Content Generation (GPT-4o-mini): ✅")
    print(f"  - Image Generation (Gemini 2.5 Flash): ✅")
    print(f"  - Prompt Management: ✅")
    print(f"  - Batch Processing: ✅")
    print(f"  - Wizard Mode (Guided Creation): ✅")
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
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )