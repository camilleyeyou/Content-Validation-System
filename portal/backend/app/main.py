from __future__ import annotations

import os
import uuid
import time
import logging
import json
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

# Session secret (stable across restarts)
SESSION_SECRET = os.getenv("SESSION_SECRET")
if not SESSION_SECRET:
    import hashlib
    deployment_id = os.getenv("RAILWAY_DEPLOYMENT_ID", "local-dev")
    SESSION_SECRET = hashlib.sha256(f"portal-secret-{deployment_id}".encode()).hexdigest()
    logger.warning("SESSION_SECRET not set - using deployment-based secret. SET THIS IN PRODUCTION!")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="none",       # cross-site
    https_only=True,        # required with SameSite=None
    max_age=60 * 60 * 24 * 7,
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

# In-memory fallback storage (temporary workaround)
FALLBACK_STORAGE: Dict[str, Any] = {}

# --- OpenAI config -------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def _openai_enabled() -> bool:
    if not OPENAI_API_KEY:
        return False
    try:
        # Delay import so missing package won't crash server start
        import openai  # noqa: F401
        return True
    except Exception:
        logger.warning("OpenAI not available: package not installed or import failed.")
        return False

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

# Controls for generation (all optional – keeps old UI working)
class RunBatchIn(BaseModel):
    topics: Optional[List[str]] = None
    count: Optional[int] = 3
    tone: Optional[str] = "professional, friendly"
    audience: Optional[str] = "engineers, founders, and product leaders"
    language: Optional[str] = "English"
    constraints: Optional[str] = "Max ~1200 chars. Include 2–5 relevant hashtags (no # symbol). Avoid emojis unless clearly helpful."

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def get_session_key(request: Request) -> str:
    session_id = request.session.get("portal_session_id")
    if not session_id:
        session_id = uuid.uuid4().hex
        request.session["portal_session_id"] = session_id
    return session_id

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
    fallback_key = f"{session_key}_{key}"
    FALLBACK_STORAGE[fallback_key] = items
    logger.info(f"Saved {len(items)} items to {key} for session {session_key}")

# ------------------------------------------------------------------------------
# OpenAI Generation
# ------------------------------------------------------------------------------

def _generate_posts_openai(
    topics: List[str],
    count: int,
    tone: str,
    audience: str,
    language: str,
    constraints: str,
) -> List[Dict[str, Any]]:
    """
    Calls OpenAI to create LinkedIn-style posts.
    Returns list of dicts with keys: id, content, hashtags, status, created_at, li_post_id, error_message
    """
    if not _openai_enabled():
        raise RuntimeError("OpenAI not configured")

    from openai import OpenAI  # type: ignore

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Build a strict instruction to return JSON we can parse
    system = (
        "You are a helpful assistant that drafts LinkedIn posts.\n"
        "Return ONLY valid JSON with this shape:\n"
        '{ "posts": [ { "content": "<text>", "hashtags": ["TagOne","TagTwo"] }, ... ] }\n'
        f"Target audience: {audience}. Tone: {tone}. Language: {language}.\n"
        f"Constraints: {constraints}\n"
        "Do not include URLs unless necessary. No markdown, no code blocks."
    )

    user_payload = {
        "topics": topics,
        "count": count,
    }

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user_payload)},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        posts = data.get("posts", [])
        if not isinstance(posts, list) or not posts:
            raise ValueError("No posts in OpenAI response")

        results: List[Dict[str, Any]] = []
        for p in posts[:count]:
            content = (p.get("content") or "").strip()
            hashtags = p.get("hashtags") or []
            # Normalize hashtags to list[str] without '#'
            if isinstance(hashtags, str):
                hashtags = [h.strip().lstrip("#") for h in hashtags.split(",") if h.strip()]
            elif isinstance(hashtags, list):
                hashtags = [str(h).strip().lstrip("#") for h in hashtags if str(h).strip()]
            hashtags = hashtags[:5]

            if not content:
                continue

            results.append(
                {
                    "id": uuid.uuid4().hex,
                    "content": content,
                    "hashtags": hashtags,
                    "status": "approved",
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "li_post_id": None,
                    "error_message": None,
                }
            )

        if not results:
            raise ValueError("OpenAI returned empty content after normalization")

        return results

    except Exception as e:
        logger.error(f"OpenAI generation failed: {e}", exc_info=True)
        raise

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
        "openai_enabled": _openai_enabled(),
        "openai_model": OPENAI_MODEL if _openai_enabled() else None,
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
            f"Redirect URI mismatch - provided: {payload.redirect_uri}, expected: {expected_redirect}"
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
        "redirect_uri_correct": payload.redirect_uri.strip() == expected_redirect,
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
            status_code=400,
        )

    if redirect:
        request.session["post_login_redirect"] = redirect
    elif "post_login_redirect" not in request.session:
        request.session["post_login_redirect"] = FRONTEND_BASE_URL

    state = f"include_org:{1 if include_org else 0}"
    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization?"
        + urlencode(
            {
                "response_type": "code",
                "client_id": cfg["client_id"],
                "redirect_uri": str(cfg["redirect_uri"]),
                "scope": "openid profile email w_member_social rw_organization_admin w_organization_social",
                "state": state,
            }
        )
    )
    logger.info(f"Redirecting to LinkedIn OAuth with redirect_uri: {cfg['redirect_uri']}")
    return RedirectResponse(url=auth_url, status_code=307)

@app.get("/auth/linkedin/callback")
def linkedin_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    if error:
        logger.error(f"LinkedIn OAuth error: {error} - {error_description}")
        dest = request.session.pop("post_login_redirect", None) or FRONTEND_BASE_URL
        sep = "&" if "?" in dest else "?"
        return RedirectResponse(
            url=f"{dest}{sep}error={error}&error_description={error_description or ''}",
            status_code=307,
        )

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
            error_data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
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
        "session_id": get_session_key(request),  # Debug
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
def run_batch(request: Request, payload: Optional[RunBatchIn] = Body(default=None)):
    """
    If OPENAI_API_KEY is present and the 'openai' package is installed:
      → generate via OpenAI using optional controls (topics, count, tone, audience, language)
    Otherwise:
      → generate the same 3 demo posts as before.
    """
    session_key = get_session_key(request)
    logger.info(f"Running batch for session: {session_key}")

    existing = _session_list(request, "approved")
    logger.info(f"Existing approved posts: {len(existing)}")

    # Defaults if no payload is sent (keeps old UI happy)
    topics = (payload.topics if payload and payload.topics else ["company update", "product tip", "culture note"])
    cnt = payload.count if payload and payload.count is not None else 3
    cnt = max(1, min(int(cnt), 10))  # clamp 1..10
    tone = payload.tone if payload and payload.tone else "professional, friendly"
    audience = payload.audience if payload and payload.audience else "engineers, founders, and product leaders"
    language = payload.language if payload and payload.language else "English"
    constraints = payload.constraints if payload and payload.constraints else (
        "Max ~1200 chars. Include 2–5 relevant hashtags (no # symbol). "
        "Avoid emojis unless clearly helpful."
    )

    used_openai = False
    openai_error: Optional[str] = None
    new_items: List[Dict[str, Any]] = []

    if _openai_enabled():
        try:
            new_items = _generate_posts_openai(
                topics=topics,
                count=cnt,
                tone=tone,
                audience=audience,
                language=language,
                constraints=constraints,
            )
            used_openai = True
            logger.info(f"OpenAI generated {len(new_items)} posts")
        except Exception as e:
            openai_error = str(e)
            logger.error(f"Falling back to demo posts due to OpenAI error: {openai_error}")

    if not new_items:
        # Fallback demo posts (exact shape as before)
        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        new_items = [
            {
                "id": uuid.uuid4().hex,
                "content": f"Excited to share our latest update: the Content Validation System now supports org posting! (Generated at {time.strftime('%H:%M:%S')})",
                "hashtags": ["ProductUpdate", "LinkedInAPI"],
                "status": "approved",
                "created_at": now_str,
                "li_post_id": None,
                "error_message": None,
            },
            {
                "id": uuid.uuid4().hex,
                "content": f"Here are 5 lessons we learned shipping an end-to-end LinkedIn content pipeline. (Generated at {time.strftime('%H:%M:%S')})",
                "hashtags": ["Engineering", "LessonsLearned"],
                "status": "approved",
                "created_at": now_str,
                "li_post_id": None,
                "error_message": None,
            },
            {
                "id": uuid.uuid4().hex,
                "content": f"Now testing org drafts vs. immediate publishing — thanks for all the feedback! (Generated at {time.strftime('%H:%M:%S')})",
                "hashtags": ["Startup", "SaaS"],
                "status": "approved",
                "created_at": now_str,
                "li_post_id": None,
                "error_message": None,
            },
        ]
        logger.info(f"Generated {len(new_items)} fallback demo posts")

    # Merge into approved queue
    existing.extend(new_items)
    _save_session_list(request, "approved", existing)
    total = len(_session_list(request, "approved"))

    resp: Dict[str, Any] = {
        "approved_count": len(new_items),
        "batch_id": uuid.uuid4().hex,
        "total_in_queue": total,
        "session_id": session_key,
        "used_openai": used_openai,
    }
    if openai_error:
        resp["openai_error"] = openai_error

    return resp

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
        "openai_enabled": _openai_enabled(),
        "openai_model": OPENAI_MODEL if _openai_enabled() else None,
    }

@app.post("/api/logout")
def logout(request: Request):
    request.session.clear()
    session_key = get_session_key(request)
    keys_to_remove = [k for k in FALLBACK_STORAGE.keys() if k.startswith(f"{session_key}_")]
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
        "openai_enabled": _openai_enabled(),
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
