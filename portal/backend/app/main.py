from __future__ import annotations

import os
import uuid
import time
import logging
import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests
from fastapi import FastAPI, Request, Body, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

# ------------------------------------------------------------------------------
# Logging Setup
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# App & Config
# ------------------------------------------------------------------------------

app = FastAPI(title="Content Portal API", version="1.0.0")

# CORS (allow your Vercel site + localhost dev)
def _split_env_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]

CORS_ORIGINS = _split_env_list(
    os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,https://content-validation-system.vercel.app",
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    max_age=600,
)

# Session secret (stable even without env)
SESSION_SECRET = os.getenv("SESSION_SECRET")
if not SESSION_SECRET:
    import hashlib
    deployment_id = os.getenv("RAILWAY_DEPLOYMENT_ID", "local-dev")
    SESSION_SECRET = hashlib.sha256(f"portal-secret-{deployment_id}".encode()).hexdigest()
    logger.warning("SESSION_SECRET not set - using deployment-based secret. SET THIS IN PRODUCTION!")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="none",       # cross-site cookies for Vercel <-> Railway
    https_only=True,        # required with same_site="none"
    max_age=60 * 60 * 24 * 7,  # 7 days
)

FRONTEND_BASE_URL = (
    os.getenv("PORTAL_BASE_URL")
    or os.getenv("FRONTEND_BASE_URL")
    or "https://content-validation-system.vercel.app"
)
API_BASE_URL = os.getenv("API_BASE_URL") or ""

# Railway/deployment URL for redirect URI
DEPLOYMENT_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if DEPLOYMENT_URL:
    DEPLOYMENT_URL = f"https://{DEPLOYMENT_URL}"
else:
    DEPLOYMENT_URL = os.getenv("API_PUBLIC_URL", "http://localhost:8080")

# OpenAI config (used for real generation)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# In-memory fallback storage (session shadow)
FALLBACK_STORAGE: Dict[str, Any] = {}

# ------------------------------------------------------------------------------
# Models
# ------------------------------------------------------------------------------

class LinkedInSettingsIn(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str

class LinkedInSettingsOut(BaseModel):
    client_id: Optional[str] = None
    redirect_uri: Optional[str] = None
    has_secret: bool = False
    portal_base_url: Optional[str] = None
    api_base: Optional[str] = None
    suggested_redirect_uri: Optional[str] = None
    deployment_url: Optional[str] = None

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    help: Optional[str] = None

# Optional: request body for generation (dashboard currently sends `{}`)
class GenerateIn(BaseModel):
    topic: Optional[str] = None
    tone: Optional[str] = None
    audience: Optional[str] = None
    count: Optional[int] = 3  # default 3

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def get_session_key(request: Request) -> str:
    sid = request.session.get("portal_session_id")
    if not sid:
        sid = uuid.uuid4().hex
        request.session["portal_session_id"] = sid
    return sid

def get_linkedin_settings_from_env() -> Optional[Dict[str, str]]:
    cid = os.getenv("LINKEDIN_CLIENT_ID")
    csec = os.getenv("LINKEDIN_CLIENT_SECRET")
    ruri = os.getenv("LINKEDIN_REDIRECT_URI")
    if cid and csec and ruri:
        return {"client_id": cid, "client_secret": csec, "redirect_uri": ruri}
    return None

def get_linkedin_settings(request: Request) -> Optional[Dict[str, str]]:
    sess = request.session.get("linkedin_settings")
    if isinstance(sess, dict) and "client_id" in sess and "client_secret" in sess and "redirect_uri" in sess:
        return sess
    return get_linkedin_settings_from_env()

def ensure_logged_in(request: Request) -> Dict[str, Any]:
    token = request.session.get("li_token")
    if not token:
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated. Please connect your LinkedIn account first."
        )
    return token

def _session_list(request: Request, key: str) -> List[Dict[str, Any]]:
    session_key = get_session_key(request)
    value = request.session.get(key)
    if isinstance(value, list):
        return value
    fallback_key = f"{session_key}_{key}"
    if fallback_key in FALLBACK_STORAGE:
        return FALLBACK_STORAGE[fallback_key]
    return []

def _save_session_list(request: Request, key: str, items: List[Dict[str, Any]]) -> None:
    session_key = get_session_key(request)
    request.session[key] = items
    FALLBACK_STORAGE[f"{session_key}_{key}"] = items
    logger.info(f"Saved {len(items)} items to {key} for session {session_key}")

# ---- OpenAI helpers ----------------------------------------------------------

def _extract_json_array(text: str) -> List[Dict[str, Any]]:
    """
    Attempts to extract a JSON array from a model response, even if the model
    adds prose or code fences.
    """
    # Try direct parse first
    try:
        val = json.loads(text)
        if isinstance(val, list):
            return val
        if isinstance(val, dict) and "posts" in val and isinstance(val["posts"], list):
            return val["posts"]
    except Exception:
        pass

    # Find first [...] block
    m = re.search(r"\[\s*{.*}\s*\]", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass

    # Find {"posts":[...]}
    m = re.search(r'{"posts"\s*:\s*\[\s*{.*}\s*\]}', text, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            return obj.get("posts", [])
        except Exception:
            pass

    raise ValueError("Could not parse model output as JSON")

def generate_posts_via_openai(count: int = 3, topic: Optional[str] = None,
                              tone: Optional[str] = None, audience: Optional[str] = None) -> List[Dict[str, Any]]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")

    # Build prompt
    topic_txt = topic or "product updates and engineering insights for a SaaS startup"
    tone_txt = tone or "concise, knowledgeable, positive, non-salesy"
    audience_txt = audience or "LinkedIn professionals in product, growth, and engineering"

    system = (
        "You are a social media assistant that writes high-signal LinkedIn posts. "
        "You only return valid JSON — no markdown, no backticks, no extra text."
    )
    user = (
        f"Generate {count} LinkedIn posts about: {topic_txt}.\n"
        f"Tone: {tone_txt}.\nAudience: {audience_txt}.\n"
        "Return a JSON object with key 'posts' whose value is an array of objects. "
        "Each object must have:\n"
        "  - content: string (2–4 sentences, no hashtags inside, no emojis)\n"
        "  - hashtags: array of 2–5 strings (do NOT include the # character in the strings)\n"
        "Example shape:\n"
        '{"posts":[{"content":"...","hashtags":["ProductUpdate","SaaS"]}]}'
    )

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.7,
                "max_tokens": 900,
            },
            timeout=45,
        )
        if not resp.ok:
            raise RuntimeError(f"OpenAI error: {resp.status_code} {resp.text[:200]}")
        data = resp.json()
        raw = data["choices"][0]["message"]["content"]
        posts = _extract_json_array(raw)
        # Normalize / sanitize
        norm: List[Dict[str, Any]] = []
        for p in posts[:count]:
            content = str(p.get("content", "")).strip()
            hashtags = p.get("hashtags", [])
            if not isinstance(hashtags, list):
                hashtags = []
            # normalize hashtag items, strip leading # and spaces
            hashtags = [str(h).lstrip("#").strip() for h in hashtags if str(h).strip()]
            if content:
                norm.append({
                    "id": uuid.uuid4().hex,
                    "content": content,
                    "hashtags": hashtags[:5],
                    "status": "approved",
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "li_post_id": None,
                    "error_message": None,
                })
        return norm
    except Exception as e:
        logger.error(f"OpenAI generation failed: {e}")
        raise

def generate_posts_fallback(count: int = 3) -> List[Dict[str, Any]]:
    # Keep a simple, deterministic fallback so UI still works
    samples: List[Dict[str, Any]] = []
    templates = [
        "Excited to share our latest update: the Content Validation System now supports org posting!",
        "Here are 5 lessons we learned shipping an end-to-end LinkedIn content pipeline.",
        "Now testing org drafts vs. immediate publishing — thanks for all the feedback!",
    ]
    for i in range(count):
        text = templates[i % len(templates)]
        samples.append({
            "id": uuid.uuid4().hex,
            "content": f"{text} (Generated at {time.strftime('%H:%M:%S')})",
            "hashtags": ["ProductUpdate", "LinkedInAPI"] if i == 0 else (["Engineering", "LessonsLearned"] if i == 1 else ["Startup", "SaaS"]),
            "status": "approved",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "li_post_id": None,
            "error_message": None,
        })
    return samples

# ------------------------------------------------------------------------------
# Root & health
# ------------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Content Portal API",
        "portal_base_url": FRONTEND_BASE_URL,
        "api_base": API_BASE_URL or "auto",
        "deployment_url": DEPLOYMENT_URL,
        "suggested_redirect_uri": f"{DEPLOYMENT_URL}/auth/linkedin/callback",
        "session_configured": bool(SESSION_SECRET),
    }

@app.get("/api/health")
def health():
    return {"ok": True, "time": int(time.time())}

# ------------------------------------------------------------------------------
# LinkedIn Settings
# ------------------------------------------------------------------------------

@app.options("/api/settings/linkedin")
def options_settings_linkedin():
    return JSONResponse({"ok": True})

@app.get("/api/settings/linkedin", response_model=LinkedInSettingsOut)
def get_settings_linkedin(request: Request):
    cfg = get_linkedin_settings(request)
    suggested_redirect = f"{DEPLOYMENT_URL}/auth/linkedin/callback"
    
    return LinkedInSettingsOut(
        client_id=cfg.get("client_id") if cfg else None,
        redirect_uri=cfg.get("redirect_uri") if cfg else None,
        has_secret=bool(cfg and cfg.get("client_secret")),
        portal_base_url=FRONTEND_BASE_URL,
        api_base=API_BASE_URL or "auto",
        suggested_redirect_uri=suggested_redirect,
        deployment_url=DEPLOYMENT_URL,
    )

@app.post("/api/settings/linkedin")
def post_settings_linkedin(payload: LinkedInSettingsIn, request: Request):
    if not payload.client_id.strip():
        raise HTTPException(status_code=400, detail="Client ID is required")
    if not payload.client_secret.strip():
        raise HTTPException(status_code=400, detail="Client Secret is required")
    if not payload.redirect_uri.strip():
        raise HTTPException(status_code=400, detail="Redirect URI is required")
    
    expected_redirect = f"{DEPLOYMENT_URL}/auth/linkedin/callback"
    if payload.redirect_uri.strip() != expected_redirect:
        logger.warning(
            f"Redirect URI mismatch - provided: {payload.redirect_uri}, "
            f"expected: {expected_redirect}"
        )
    
    request.session["linkedin_settings"] = {
        "client_id": payload.client_id.strip(),
        "client_secret": payload.client_secret.strip(),
        "redirect_uri": payload.redirect_uri.strip(),
    }
    
    logger.info(f"LinkedIn settings saved for session with client_id: {payload.client_id[:8]}...")
    
    return {
        "ok": True, 
        "message": "LinkedIn settings saved to session",
        "redirect_uri_correct": payload.redirect_uri.strip() == expected_redirect
    }

# ------------------------------------------------------------------------------
# LinkedIn OAuth
# ------------------------------------------------------------------------------

@app.get("/auth/linkedin/login")
def linkedin_login(request: Request, include_org: bool = False, redirect: Optional[str] = None):
    cfg = get_linkedin_settings(request)
    if not cfg:
        logger.error("LinkedIn login attempted without settings configured")
        return JSONResponse(
            {"detail": "LinkedIn settings are missing", "help": "Please configure your LinkedIn app credentials in Settings first"}, 
            status_code=400
        )

    if redirect:
        request.session["post_login_redirect"] = redirect
    elif "post_login_redirect" not in request.session:
        request.session["post_login_redirect"] = FRONTEND_BASE_URL

    state = f"include_org:{1 if include_org else 0}"

    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization?"
        + urlencode({
            "response_type": "code",
            "client_id": cfg["client_id"],
            "redirect_uri": str(cfg["redirect_uri"]),
            "scope": "openid profile email w_member_social rw_organization_admin w_organization_social",
            "state": state,
        })
    )
    
    logger.info(f"Redirecting to LinkedIn OAuth with redirect_uri: {cfg['redirect_uri']}")
    return RedirectResponse(url=auth_url, status_code=307)

@app.get("/auth/linkedin/callback")
def linkedin_callback(
    request: Request, 
    code: Optional[str] = None, 
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None
):
    if error:
        logger.error(f"LinkedIn OAuth error: {error} - {error_description}")
        dest = request.session.pop("post_login_redirect", None) or FRONTEND_BASE_URL
        sep = "&" if "?" in dest else "?"
        return RedirectResponse(url=f"{dest}{sep}error={error}&error_description={error_description or ''}", status_code=307)
    
    if not code:
        logger.error("LinkedIn callback without code parameter")
        return JSONResponse({"detail": "Missing authorization code"}, status_code=400)
    
    cfg = get_linkedin_settings(request)
    if not cfg:
        logger.error("LinkedIn callback attempted without settings")
        return JSONResponse({"detail": "LinkedIn settings are missing"}, status_code=400)

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": str(cfg["redirect_uri"]),
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
    }

    try:
        logger.info(f"Exchanging code for token with redirect_uri: {cfg['redirect_uri']}")
        r = requests.post(token_url, data=data, timeout=20)
        
        if not r.ok:
            error_data = r.json() if r.headers.get('content-type', '').startswith('application/json') else {}
            logger.error(f"Token exchange failed: {r.status_code} - {error_data}")
            return JSONResponse({"detail": f"Token exchange failed: {r.text[:200]}"}, status_code=400)
        
        token = r.json()
        logger.info("Successfully obtained access token")
        
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        return JSONResponse({"detail": f"Token exchange failed: {str(e)}"}, status_code=400)

    profile: Dict[str, Any] = {}
    try:
        ui = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {token.get('access_token')}"},
            timeout=15,
        )
        if ui.ok:
            profile = ui.json()
            logger.info(f"Retrieved profile for user: {profile.get('name', 'Unknown')}")
    except Exception as e:
        logger.warning(f"Failed to fetch user profile: {e}")

    request.session["li_token"] = token
    if profile:
        request.session["li_profile"] = profile

    dest = request.session.pop("post_login_redirect", None) or FRONTEND_BASE_URL or "/"
    sep = "&" if "?" in dest else "?"
    
    logger.info(f"Authentication successful, redirecting to: {dest}")
    return RedirectResponse(url=f"{dest}{sep}app_session=1&success=true", status_code=307)

# ------------------------------------------------------------------------------
# Me / Orgs
# ------------------------------------------------------------------------------

@app.options("/api/me")
def options_me():
    return JSONResponse({"ok": True})

@app.get("/api/me")
def api_me(request: Request):
    token = request.session.get("li_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    prof = request.session.get("li_profile") or {}
    sub = prof.get("sub") or "linkedin-user"
    name = prof.get("name") or prof.get("given_name") or "LinkedIn User"
    email = prof.get("email") or prof.get("email_verified") or None

    return {
        "sub": sub, 
        "name": name, 
        "email": email, 
        "org_preferred": request.session.get("org_preferred"),
        "token_expires_in": token.get("expires_in"),
        "session_id": get_session_key(request),
    }

@app.options("/api/orgs")
def options_orgs():
    return JSONResponse({"ok": True})

@app.get("/api/orgs")
def api_orgs(request: Request):
    token = request.session.get("li_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = token.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Missing access token")

    try:
        url = (
            "https://api.linkedin.com/v2/organizationAcls"
            "?q=roleAssignee&role=ADMINISTRATOR&state=APPROVED"
            "&projection=(elements*(organization~(id,localizedName,vanityName)))"
        )
        resp = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=15)
        
        if not resp.ok:
            return JSONResponse({"error": "Cannot fetch organizations"}, status_code=resp.status_code)
        
        data = resp.json()
        orgs: List[Dict[str, str]] = []
        for el in data.get("elements", []):
            org = el.get("organization~") or {}
            oid = str(org.get("id") or "")
            urn = f"urn:li:organization:{oid}" if oid else ""
            if oid:
                orgs.append({"id": oid, "urn": urn})
        
        logger.info(f"Found {len(orgs)} organizations for user")
        return {"orgs": orgs}
        
    except Exception as e:
        logger.error(f"Error fetching organizations: {e}")
        return {"orgs": []}

# ------------------------------------------------------------------------------
# Approved queue
# ------------------------------------------------------------------------------

@app.options("/api/approved")
def options_approved():
    return JSONResponse({"ok": True})

@app.get("/api/approved")
def get_approved(request: Request):
    session_key = get_session_key(request)
    logger.info(f"Getting approved for session: {session_key}")
    items = _session_list(request, "approved")
    logger.info(f"Returning {len(items)} approved posts")
    return items

class PublishIn(BaseModel):
    ids: List[str]
    target: str  # "MEMBER" | "ORG"
    publish_now: bool = True
    org_id: Optional[str] = None

@app.post("/api/approved/publish")
def post_publish(request: Request, payload: PublishIn):
    ensure_logged_in(request)
    
    if not payload.ids:
        raise HTTPException(status_code=400, detail="No posts selected")
    if payload.target not in {"MEMBER", "ORG"}:
        raise HTTPException(status_code=400, detail="Invalid publish target")

    items = _session_list(request, "approved")
    idset = set(payload.ids)

    success = 0
    results: List[Dict[str, Any]] = []

    for it in items:
        if it.get("id") in idset:
            it["status"] = "published" if payload.publish_now else "draft"
            it["li_post_id"] = it.get("li_post_id") or f"mock-{uuid.uuid4().hex[:12]}"
            it["published_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            it["published_as"] = payload.target
            if payload.target == "ORG":
                it["published_org_id"] = payload.org_id
            
            success += 1
            results.append({"id": it["id"], "status": it["status"], "li_post_id": it["li_post_id"]})

    _save_session_list(request, "approved", items)
    logger.info(f"Published {success}/{len(payload.ids)} posts as {payload.target}")
    return {"successful": success, "results": results}

@app.post("/api/approved/clear")
def post_clear(request: Request):
    items = _session_list(request, "approved")
    deleted = len(items)
    _save_session_list(request, "approved", [])
    logger.info(f"Cleared {deleted} approved posts")
    return {"deleted": deleted}

# ------------------------------------------------------------------------------
# Run pipeline (OpenAI-backed with fallback)
# ------------------------------------------------------------------------------

@app.options("/api/run-batch")
def options_run_batch():
    return JSONResponse({"ok": True})

@app.post("/api/run-batch")
def run_batch(request: Request, body: GenerateIn = Body(default=GenerateIn())):
    """
    Generates approved posts using OpenAI when OPENAI_API_KEY is available.
    Falls back to deterministic samples if not available or if generation fails.
    """
    session_key = get_session_key(request)
    logger.info(f"Running batch for session: {session_key}")

    existing = _session_list(request, "approved")
    logger.info(f"Existing approved posts: {len(existing)}")

    # Try OpenAI first
    new_items: List[Dict[str, Any]] = []
    used_openai = False
    try:
        if OPENAI_API_KEY:
            used_openai = True
            new_items = generate_posts_via_openai(
                count=max(1, min(10, body.count or 3)),
                topic=body.topic,
                tone=body.tone,
                audience=body.audience,
            )
        else:
            logger.warning("OPENAI_API_KEY not set — using fallback samples")
            new_items = generate_posts_fallback(count=max(1, min(10, body.count or 3)))
    except Exception:
        # If OpenAI fails for any reason, fall back so the UI stays usable
        logger.warning("Falling back to sample posts due to generation error")
        new_items = generate_posts_fallback(count=max(1, min(10, body.count or 3)))

    existing.extend(new_items)
    _save_session_list(request, "approved", existing)

    verify = _session_list(request, "approved")
    logger.info(f"After saving: {len(verify)} total approved posts")

    return {
        "approved_count": len(new_items),
        "batch_id": uuid.uuid4().hex,
        "total_in_queue": len(verify),
        "session_id": session_key,
        "used_openai": used_openai,
    }

# ------------------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------------------

@app.get("/api/config")
def api_config():
    return {
        "portal_base_url": FRONTEND_BASE_URL,
        "api_base": API_BASE_URL or "auto",
        "deployment_url": DEPLOYMENT_URL,
        "suggested_redirect_uri": f"{DEPLOYMENT_URL}/auth/linkedin/callback",
        "cors_allow_origins": CORS_ORIGINS,
        "session_configured": bool(os.getenv("SESSION_SECRET")),
        "openai_enabled": bool(OPENAI_API_KEY),
        "openai_model": OPENAI_MODEL if OPENAI_API_KEY else None,
    }

@app.post("/api/logout")
def logout(request: Request):
    request.session.clear()
    # Clear fallback storage for this session
    session_key = get_session_key(request)
    keys_to_remove = [k for k in list(FALLBACK_STORAGE.keys()) if k.startswith(f"{session_key}_")]
    for k in keys_to_remove:
        del FALLBACK_STORAGE[k]
    logger.info("User logged out")
    return {"ok": True, "message": "Logged out successfully"}

@app.get("/api/debug/session")
def debug_session(request: Request):
    session_key = get_session_key(request)
    return {
        "session_id": session_key,
        "session_keys": list(request.session.keys()),
        "approved_count": len(_session_list(request, "approved")),
        "is_authenticated": bool(request.session.get("li_token")),
        "fallback_storage_keys": [k for k in FALLBACK_STORAGE.keys() if k.startswith(f"{session_key}_")],
    }

# ------------------------------------------------------------------------------
# Error handlers
# ------------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "An internal error occurred"})
