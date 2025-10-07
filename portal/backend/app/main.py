from __future__ import annotations

import os
import uuid
import time
import logging
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

# Sessions (Enhanced for cross-site with better security)
SESSION_SECRET = os.getenv("SESSION_SECRET")
if not SESSION_SECRET:
    logger.warning("SESSION_SECRET not set - using dev secret. Set this in production!")
    SESSION_SECRET = "dev-secret-change-me-in-production"

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="none",       # Required for cross-site cookies
    https_only=True,        # Required when same_site="none"
    max_age=60 * 60 * 24 * 7,  # 7 days
    domain=None,            # Don't set domain to work across sites
)

FRONTEND_BASE_URL = (
    os.getenv("PORTAL_BASE_URL")
    or os.getenv("FRONTEND_BASE_URL")
    or "https://content-validation-system.vercel.app"
)
API_BASE_URL = os.getenv("API_BASE_URL") or ""  # purely informational

# Railway/deployment URL for redirect URI
DEPLOYMENT_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if DEPLOYMENT_URL:
    DEPLOYMENT_URL = f"https://{DEPLOYMENT_URL}"
else:
    DEPLOYMENT_URL = os.getenv("API_PUBLIC_URL", "http://localhost:8080")

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

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def get_linkedin_settings_from_env() -> Optional[Dict[str, str]]:
    cid = os.getenv("LINKEDIN_CLIENT_ID")
    csec = os.getenv("LINKEDIN_CLIENT_SECRET")
    ruri = os.getenv("LINKEDIN_REDIRECT_URI")
    if cid and csec and ruri:
        return {"client_id": cid, "client_secret": csec, "redirect_uri": ruri}
    return None

def get_linkedin_settings(request: Request) -> Optional[Dict[str, str]]:
    # 1) per-session overrides (set via POST /api/settings/linkedin)
    sess = request.session.get("linkedin_settings")
    if isinstance(sess, dict) and "client_id" in sess and "client_secret" in sess and "redirect_uri" in sess:
        return sess
    # 2) process-wide env fallback
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
    value = request.session.get(key)
    if not isinstance(value, list):
        value = []
    return value

def _save_session_list(request: Request, key: str, items: List[Dict[str, Any]]) -> None:
    request.session[key] = items

# ------------------------------------------------------------------------------
# Root & health
# ------------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Content Portal API – use /auth/linkedin/login or the UI",
        "portal_base_url": FRONTEND_BASE_URL,
        "api_base": API_BASE_URL or "auto",
        "deployment_url": DEPLOYMENT_URL,
        "suggested_redirect_uri": f"{DEPLOYMENT_URL}/auth/linkedin/callback"
    }

@app.get("/api/health")
def health():
    return {"ok": True, "time": int(time.time())}

# ------------------------------------------------------------------------------
# LinkedIn Settings (front-end configurable)
# ------------------------------------------------------------------------------

@app.options("/api/settings/linkedin")
def options_settings_linkedin():
    # CORS handled by middleware; explicit 200 helps some proxies.
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
    # Validate the settings
    if not payload.client_id.strip():
        raise HTTPException(status_code=400, detail="Client ID is required")
    if not payload.client_secret.strip():
        raise HTTPException(status_code=400, detail="Client Secret is required")
    if not payload.redirect_uri.strip():
        raise HTTPException(status_code=400, detail="Redirect URI is required")
    
    # Warn if redirect URI doesn't match expected pattern
    expected_redirect = f"{DEPLOYMENT_URL}/auth/linkedin/callback"
    if payload.redirect_uri.strip() != expected_redirect:
        logger.warning(
            f"Redirect URI mismatch - provided: {payload.redirect_uri}, "
            f"expected: {expected_redirect}"
        )
    
    # Store into the session so each user can bring their own LinkedIn app.
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
            {
                "detail": "LinkedIn settings are missing",
                "help": "Please configure your LinkedIn app credentials in Settings first"
            }, 
            status_code=400
        )

    # remember where to return after callback
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
                "redirect_uri": str(cfg["redirect_uri"]),  # ensure plain str
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
    error_description: Optional[str] = None
):
    # Handle OAuth errors from LinkedIn
    if error:
        logger.error(f"LinkedIn OAuth error: {error} - {error_description}")
        error_message = f"LinkedIn authorization failed: {error}"
        
        if error == "user_cancelled_authorize":
            error_message = "Authorization cancelled by user"
        elif error == "unauthorized_scope_error":
            error_message = "The requested permissions were not granted. Please ensure you've approved all required scopes."
        
        # Redirect to frontend with error
        dest = request.session.pop("post_login_redirect", None) or FRONTEND_BASE_URL
        sep = "&" if "?" in dest else "?"
        return RedirectResponse(
            url=f"{dest}{sep}error={error}&error_description={error_description or ''}", 
            status_code=307
        )
    
    if not code:
        logger.error("LinkedIn callback without code parameter")
        return JSONResponse(
            {"detail": "Missing authorization code", "help": "LinkedIn didn't provide an authorization code"}, 
            status_code=400
        )
    
    cfg = get_linkedin_settings(request)
    if not cfg:
        logger.error("LinkedIn callback attempted without settings")
        return JSONResponse(
            {"detail": "LinkedIn settings are missing", "help": "Session may have expired. Please reconfigure settings."}, 
            status_code=400
        )

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": str(cfg["redirect_uri"]),  # avoid AnyHttpUrl problem
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
    }

    try:
        logger.info(f"Exchanging code for token with redirect_uri: {cfg['redirect_uri']}")
        r = requests.post(token_url, data=data, timeout=20)
        
        if not r.ok:
            error_data = r.json() if r.headers.get('content-type', '').startswith('application/json') else {}
            logger.error(f"Token exchange failed: {r.status_code} - {error_data}")
            
            # Common error handling
            if "error" in error_data:
                if error_data["error"] == "invalid_request":
                    return JSONResponse(
                        {
                            "detail": "Invalid request to LinkedIn",
                            "error": error_data.get("error_description", "Unknown error"),
                            "help": "This usually means the redirect_uri doesn't match exactly. Check your LinkedIn app settings."
                        },
                        status_code=400
                    )
                elif error_data["error"] == "invalid_client":
                    return JSONResponse(
                        {
                            "detail": "Invalid client credentials",
                            "help": "Check that your Client ID and Client Secret are correct"
                        },
                        status_code=400
                    )
            
            return JSONResponse(
                {"detail": f"Token exchange failed: {r.text[:200]}"}, 
                status_code=400
            )
        
        token = r.json()  # access_token, expires_in, (maybe) id_token
        logger.info("Successfully obtained access token")
        
    except requests.RequestException as e:
        logger.error(f"Network error during token exchange: {e}")
        return JSONResponse(
            {"detail": f"Network error during token exchange: {str(e)}"}, 
            status_code=500
        )
    except Exception as e:
        logger.error(f"Unexpected error during token exchange: {e}")
        return JSONResponse(
            {"detail": f"Token exchange failed: {str(e)}"}, 
            status_code=400
        )

    # Try to grab user info (best-effort)
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
        else:
            logger.warning(f"Failed to fetch user profile: {ui.status_code}")
    except Exception as e:
        logger.warning(f"Failed to fetch user profile: {e}")

    # stash both
    request.session["li_token"] = token
    if profile:
        request.session["li_profile"] = profile

    # bounce back to where the user started
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

    # return cached profile if we have one
    prof = request.session.get("li_profile") or {}
    sub = prof.get("sub") or "linkedin-user"
    name = prof.get("name") or prof.get("given_name") or "LinkedIn User"
    email = prof.get("email") or prof.get("email_verified") or None

    return {
        "sub": sub, 
        "name": name, 
        "email": email, 
        "org_preferred": request.session.get("org_preferred"),
        "token_expires_in": token.get("expires_in")
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

    # best-effort call to LinkedIn Organizations (will succeed only if scopes granted)
    try:
        # This projection returns organization IDs and names when permissions allow.
        url = (
            "https://api.linkedin.com/v2/organizationAcls"
            "?q=roleAssignee&role=ADMINISTRATOR&state=APPROVED"
            "&projection=(elements*(organization~(id,localizedName,vanityName)))"
        )
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        
        if not resp.ok:
            error_data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {}
            logger.warning(f"Cannot fetch organizations: {resp.status_code} - {error_data}")
            
            # Provide helpful error messages
            if resp.status_code == 403:
                return JSONResponse(
                    {
                        "error": "Missing organization permissions",
                        "help": "You need to request 'Advertising API' product in your LinkedIn app"
                    }, 
                    status_code=403
                )
            
            # front-end tolerates 400/401/403 here; don't crash.
            return JSONResponse(
                {"error": "Cannot fetch organizations", "details": error_data}, 
                status_code=resp.status_code
            )
        
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
        
    except requests.RequestException as e:
        logger.error(f"Network error fetching organizations: {e}")
        return JSONResponse(
            {"error": "Network error fetching organizations"}, 
            status_code=500
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching organizations: {e}")
        # quietly degrade
        return {"orgs": []}

# ------------------------------------------------------------------------------
# Approved queue (session-scoped demo storage)
# ------------------------------------------------------------------------------

@app.options("/api/approved")
def options_approved():
    return JSONResponse({"ok": True})

@app.get("/api/approved")
def get_approved(request: Request):
    # Allowed even if not logged in (UI shows content but disables publish)
    items = _session_list(request, "approved")
    return items

class PublishIn(BaseModel):
    ids: List[str]
    target: str  # "MEMBER" | "ORG"
    publish_now: bool = True
    org_id: Optional[str] = None

@app.post("/api/approved/publish")
def post_publish(request: Request, payload: PublishIn):
    # Require login to publish
    ensure_logged_in(request)
    
    if not payload.ids:
        raise HTTPException(status_code=400, detail="No posts selected for publishing")
    
    if payload.target not in ["MEMBER", "ORG"]:
        raise HTTPException(status_code=400, detail="Invalid target. Must be 'MEMBER' or 'ORG'")
    
    if payload.target == "ORG" and not payload.org_id:
        raise HTTPException(status_code=400, detail="Organization ID required for org publishing")
    
    items = _session_list(request, "approved")
    idset = set(payload.ids)

    success = 0
    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for it in items:
        if it.get("id") in idset:
            try:
                # In a real implementation, this would call LinkedIn's API
                # For demo, we just update the status
                it["status"] = "published" if payload.publish_now else "draft"
                it["li_post_id"] = it.get("li_post_id") or f"mock-{uuid.uuid4().hex[:12]}"
                it["published_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                it["published_as"] = payload.target
                if payload.target == "ORG":
                    it["published_org_id"] = payload.org_id
                
                success += 1
                results.append({
                    "id": it["id"], 
                    "status": it["status"], 
                    "li_post_id": it["li_post_id"]
                })
                
            except Exception as e:
                logger.error(f"Failed to publish post {it['id']}: {e}")
                it["error_message"] = str(e)
                errors.append({"id": it["id"], "error": str(e)})

    _save_session_list(request, "approved", items)
    
    response = {
        "successful": success, 
        "results": results,
        "total_requested": len(payload.ids)
    }
    
    if errors:
        response["errors"] = errors
    
    logger.info(f"Published {success}/{len(payload.ids)} posts as {payload.target}")
    return response

@app.post("/api/approved/clear")
def post_clear(request: Request):
    items = _session_list(request, "approved")
    deleted = len(items)
    _save_session_list(request, "approved", [])
    logger.info(f"Cleared {deleted} approved posts")
    return {"deleted": deleted}

# ------------------------------------------------------------------------------
# Run pipeline (demo generator so the UI works out-of-the-box)
# ------------------------------------------------------------------------------

@app.options("/api/run-batch")
def options_run_batch():
    return JSONResponse({"ok": True})

@app.post("/api/run-batch")
def run_batch(request: Request):
    # In your real system this would run the full pipeline. Here we just create demo items.
    existing = _session_list(request, "approved")

    # Generate a few sample posts
    samples = [
        {
            "id": uuid.uuid4().hex,
            "content": "Excited to share our latest update: the Content Validation System now supports org posting!",
            "hashtags": ["ProductUpdate", "LinkedInAPI"],
            "status": "approved",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "li_post_id": None,
            "error_message": None,
        },
        {
            "id": uuid.uuid4().hex,
            "content": "Here are 5 lessons we learned shipping an end-to-end LinkedIn content pipeline.",
            "hashtags": ["Engineering", "LessonsLearned"],
            "status": "approved",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "li_post_id": None,
            "error_message": None,
        },
        {
            "id": uuid.uuid4().hex,
            "content": "Now testing org drafts vs. immediate publishing — thanks for all the feedback!",
            "hashtags": ["Startup", "SaaS"],
            "status": "approved",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "li_post_id": None,
            "error_message": None,
        },
    ]

    existing.extend(samples)
    _save_session_list(request, "approved", existing)
    
    logger.info(f"Generated {len(samples)} approved posts")
    return {"approved_count": len(samples), "batch_id": uuid.uuid4().hex}

# ------------------------------------------------------------------------------
# Utility endpoints
# ------------------------------------------------------------------------------

@app.get("/api/config")
def api_config():
    return {
        "portal_base_url": FRONTEND_BASE_URL,
        "api_base": API_BASE_URL or "auto",
        "deployment_url": DEPLOYMENT_URL,
        "suggested_redirect_uri": f"{DEPLOYMENT_URL}/auth/linkedin/callback",
        "cors_allow_origins": CORS_ORIGINS,
    }

@app.post("/api/logout")
def logout(request: Request):
    # Clear the session
    request.session.clear()
    logger.info("User logged out")
    return {"ok": True, "message": "Logged out successfully"}

# ------------------------------------------------------------------------------
# Error handlers
# ------------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )