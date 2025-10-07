from __future__ import annotations

import os
import uuid
import time
import hmac
import json
import base64
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("portal.backend.app.main")

# ------------------------------------------------------------------------------
# App / CORS / Sessions
# ------------------------------------------------------------------------------
app = FastAPI(title="Content Portal API", version="1.1.0")

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

SESSION_SECRET = os.getenv("SESSION_SECRET")
if not SESSION_SECRET:
    logger.warning("SESSION_SECRET not set - using dev secret. Set this in production!")
    SESSION_SECRET = "dev-secret-change-me-in-production"

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="none",     # cross-site cookie support (Vercel -> Railway)
    https_only=True,      # required when same_site="none"
    max_age=60 * 60 * 24 * 7,  # 7 days
    domain=None,          # let browser scope cookie correctly
)

FRONTEND_BASE_URL = (
    os.getenv("PORTAL_BASE_URL")
    or os.getenv("FRONTEND_BASE_URL")
    or "https://content-validation-system.vercel.app"
)
API_BASE_URL = os.getenv("API_BASE_URL") or ""

DEPLOYMENT_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if DEPLOYMENT_URL:
    DEPLOYMENT_URL = f"https://{DEPLOYMENT_URL}"
else:
    DEPLOYMENT_URL = os.getenv("API_PUBLIC_URL", "http://localhost:8080")

SUGGESTED_REDIRECT = f"{DEPLOYMENT_URL}/auth/linkedin/callback"

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

class PublishIn(BaseModel):
    ids: List[str]
    target: str  # "MEMBER" | "ORG"
    publish_now: bool = True
    org_id: Optional[str] = None

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
    per_session = request.session.get("linkedin_settings")
    if isinstance(per_session, dict) and all(k in per_session for k in ("client_id", "client_secret", "redirect_uri")):
        return per_session
    return get_linkedin_settings_from_env()

def ensure_logged_in(request: Request) -> Dict[str, Any]:
    token = request.session.get("li_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated. Please connect your LinkedIn account first.")
    return token

def _session_list(request: Request, key: str) -> List[Dict[str, Any]]:
    value = request.session.get(key)
    if not isinstance(value, list):
        value = []
    return value

def _save_session_list(request: Request, key: str, items: List[Dict[str, Any]]) -> None:
    request.session[key] = items

def _nonce() -> str:
    raw = uuid.uuid4().hex.encode()
    mac = hmac.digest(SESSION_SECRET.encode(), raw, "sha256")
    return base64.urlsafe_b64encode(raw + mac[:10]).decode().rstrip("=")

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
        "suggested_redirect_uri": SUGGESTED_REDIRECT
    }

@app.get("/api/health")
def health():
    return {"ok": True, "time": int(time.time())}

# ------------------------------------------------------------------------------
# LinkedIn Settings (front-end configurable)
# ------------------------------------------------------------------------------
@app.options("/api/settings/linkedin")
def options_settings_linkedin():
    return JSONResponse({"ok": True})

@app.get("/api/settings/linkedin", response_model=LinkedInSettingsOut)
def get_settings_linkedin(request: Request):
    cfg = get_linkedin_settings(request)
    return LinkedInSettingsOut(
        client_id=cfg.get("client_id") if cfg else None,
        redirect_uri=cfg.get("redirect_uri") if cfg else None,
        has_secret=bool(cfg and cfg.get("client_secret")),
        portal_base_url=FRONTEND_BASE_URL,
        api_base=API_BASE_URL or "auto",
        suggested_redirect_uri=SUGGESTED_REDIRECT,
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

    expected = SUGGESTED_REDIRECT
    if payload.redirect_uri.strip() != expected:
        logger.warning("Redirect URI mismatch - provided: %s, expected: %s", payload.redirect_uri, expected)

    request.session["linkedin_settings"] = {
        "client_id": payload.client_id.strip(),
        "client_secret": payload.client_secret.strip(),
        "redirect_uri": payload.redirect_uri.strip(),
    }
    logger.info("LinkedIn settings saved for session with client_id: %s...", payload.client_id[:8])

    return {
        "ok": True,
        "message": "LinkedIn settings saved to session",
        "redirect_uri_correct": payload.redirect_uri.strip() == expected,
    }

# ------------------------------------------------------------------------------
# LinkedIn OAuth
# ------------------------------------------------------------------------------
@app.get("/auth/linkedin/login")
def linkedin_login(
    request: Request,
    include_org: bool | int | str = Query(default=False),
    redirect: Optional[str] = None,
):
    cfg = get_linkedin_settings(request)
    if not cfg:
        logger.error("LinkedIn login attempted without settings configured")
        return JSONResponse(
            {"detail": "LinkedIn settings are missing", "help": "Configure credentials in Settings first"},
            status_code=400,
        )

    # normalize include_org
    include_org_bool = False
    if isinstance(include_org, bool):
        include_org_bool = include_org
    else:
        include_org_bool = str(include_org).lower() in ("1", "true", "yes")

    # remember where to return after callback
    if redirect:
        request.session["post_login_redirect"] = redirect
    elif "post_login_redirect" not in request.session:
        request.session["post_login_redirect"] = FRONTEND_BASE_URL

    # CSRF-ish nonce
    nonce = _nonce()
    request.session["oauth_state_nonce"] = nonce
    state = json.dumps({"nonce": nonce, "include_org": 1 if include_org_bool else 0})

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

    logger.info("Redirecting to LinkedIn OAuth with redirect_uri: %s", cfg["redirect_uri"])
    return RedirectResponse(url=auth_url, status_code=307)

@app.get("/auth/linkedin/callback")
def linkedin_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    # OAuth error from LinkedIn
    if error:
        logger.error("LinkedIn OAuth error: %s - %s", error, error_description)
        dest = request.session.pop("post_login_redirect", None) or FRONTEND_BASE_URL
        sep = "&" if "?" in dest else "?"
        return RedirectResponse(
            url=f"{dest}{sep}error={error}&error_description={error_description or ''}",
            status_code=307,
        )

    if not code:
        return JSONResponse(
            {"detail": "Missing authorization code", "help": "LinkedIn didn't provide an authorization code"},
            status_code=400,
        )

    # Validate state/nonce best-effort
    if state:
        try:
            parsed = json.loads(state)
            sent_nonce = parsed.get("nonce")
            if sent_nonce and sent_nonce != request.session.get("oauth_state_nonce"):
                logger.warning("State nonce mismatch")
            request.session.pop("oauth_state_nonce", None)
        except Exception:
            logger.warning("Failed to parse state")

    cfg = get_linkedin_settings(request)
    if not cfg:
        return JSONResponse(
            {"detail": "LinkedIn settings are missing", "help": "Session may have expired. Reconfigure settings."},
            status_code=400,
        )

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": str(cfg["redirect_uri"]),
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
    }

    try:
        logger.info("Exchanging code for token with redirect_uri: %s", cfg["redirect_uri"])
        r = requests.post(token_url, data=data, timeout=20)
        if not r.ok:
            ctype = r.headers.get("content-type", "")
            error_data = r.json() if ctype.startswith("application/json") else {}
            logger.error("Token exchange failed: %s - %s", r.status_code, error_data)

            if isinstance(error_data, dict) and error_data.get("error") == "invalid_request":
                return JSONResponse(
                    {
                        "detail": "Invalid request to LinkedIn",
                        "error": error_data.get("error_description", "Unknown error"),
                        "help": "Redirect URI mismatch is the most common cause. Check your LinkedIn app settings.",
                    },
                    status_code=400,
                )
            if isinstance(error_data, dict) and error_data.get("error") == "invalid_client":
                return JSONResponse(
                    {"detail": "Invalid client credentials", "help": "Check Client ID and Client Secret"},
                    status_code=400,
                )
            return JSONResponse({"detail": f"Token exchange failed: {r.text[:200]}"}, status_code=400)

        token = r.json()
        logger.info("Successfully obtained access token")

    except requests.RequestException as e:
        logger.error("Network error during token exchange: %s", e)
        return JSONResponse({"detail": f"Network error during token exchange: {str(e)}"}, status_code=500)
    except Exception as e:
        logger.error("Unexpected error during token exchange: %s", e)
        return JSONResponse({"detail": f"Token exchange failed: {str(e)}"}, status_code=400)

    # Fetch user profile (best-effort)
    profile: Dict[str, Any] = {}
    try:
        ui = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {token.get('access_token')}"},
            timeout=15,
        )
        if ui.ok:
            profile = ui.json()
            logger.info("Retrieved profile for user: %s", profile.get("name", "Unknown"))
        else:
            logger.warning("Failed to fetch user profile: %s", ui.status_code)
    except Exception as e:
        logger.warning("Failed to fetch user profile: %s", e)

    request.session["li_token"] = token
    if profile:
        request.session["li_profile"] = profile

    dest = request.session.pop("post_login_redirect", None) or FRONTEND_BASE_URL or "/"
    sep = "&" if "?" in dest else "?"
    logger.info("Authentication successful, redirecting to: %s", dest)
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
    email = prof.get("email") or (prof.get("email_verified") and prof.get("email")) or None
    return {
        "ok": True,
        "sub": sub,
        "name": name,
        "email": email,
        "org_preferred": request.session.get("org_preferred"),
        "token_expires_in": token.get("expires_in"),
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
            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            logger.warning("Cannot fetch organizations: %s - %s", resp.status_code, error_data)
            if resp.status_code == 403:
                return JSONResponse(
                    {
                        "error": "Missing organization permissions",
                        "help": "You need the appropriate LinkedIn product approvals and org admin access",
                    },
                    status_code=403,
                )
            return JSONResponse({"error": "Cannot fetch organizations", "details": error_data}, status_code=resp.status_code)

        data = resp.json()
        orgs: List[Dict[str, str]] = []
        for el in data.get("elements", []):
            org = el.get("organization~") or {}
            oid = str(org.get("id") or "")
            urn = f"urn:li:organization:{oid}" if oid else ""
            if oid:
                orgs.append({"id": oid, "urn": urn})
        logger.info("Found %d organizations for user", len(orgs))
        return {"ok": True, "orgs": orgs}

    except requests.RequestException as e:
        logger.error("Network error fetching organizations: %s", e)
        return JSONResponse({"error": "Network error fetching organizations"}, status_code=500)
    except Exception as e:
        logger.error("Unexpected error fetching organizations: %s", e)
        return {"ok": True, "orgs": []}

# ------------------------------------------------------------------------------
# Approved queue (session-scoped demo storage)
# ------------------------------------------------------------------------------
@app.options("/api/approved")
def options_approved():
    return JSONResponse({"ok": True})

@app.get("/api/approved")
def get_approved(request: Request):
    items = _session_list(request, "approved")
    return {"ok": True, "count": len(items), "items": items}

@app.post("/api/approved/clear")
def post_clear(request: Request):
    items = _session_list(request, "approved")
    deleted = len(items)
    _save_session_list(request, "approved", [])
    logger.info("Cleared %d approved posts", deleted)
    return {"ok": True, "deleted": deleted}

@app.post("/api/approved/publish")
def post_publish(request: Request, payload: PublishIn):
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
                it["status"] = "published" if payload.publish_now else "draft"
                it["li_post_id"] = it.get("li_post_id") or f"mock-{uuid.uuid4().hex[:12]}"
                it["published_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                it["published_as"] = payload.target
                if payload.target == "ORG":
                    it["published_org_id"] = payload.org_id
                success += 1
                results.append({"id": it["id"], "status": it["status"], "li_post_id": it["li_post_id"]})
            except Exception as e:
                logger.error("Failed to publish post %s: %s", it.get("id"), e)
                it["error_message"] = str(e)
                errors.append({"id": it.get("id"), "error": str(e)})

    _save_session_list(request, "approved", items)
    resp: Dict[str, Any] = {"ok": True, "successful": success, "results": results, "total_requested": len(payload.ids)}
    if errors:
        resp["errors"] = errors
    logger.info("Published %d/%d posts as %s", success, len(payload.ids), payload.target)
    return resp

# ------------------------------------------------------------------------------
# Run pipeline (demo generator)
# ------------------------------------------------------------------------------
@app.options("/api/run-batch")
def options_run_batch():
    return JSONResponse({"ok": True})

@app.post("/api/run-batch")
def run_batch(request: Request, count: int = 3):
    """
    Demo generator so the UI works out-of-the-box.
    Doesn't require auth; it just seeds session 'approved' items.
    """
    existing = _session_list(request, "approved")

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    base_samples = [
        {
            "content": "Excited to share our latest update: the Content Validation System now supports org posting!",
            "hashtags": ["ProductUpdate", "LinkedInAPI"],
        },
        {
            "content": "Here are 5 lessons we learned shipping an end-to-end LinkedIn content pipeline.",
            "hashtags": ["Engineering", "LessonsLearned"],
        },
        {
            "content": "Now testing org drafts vs. immediate publishing — thanks for all the feedback!",
            "hashtags": ["Startup", "SaaS"],
        },
    ]

    # create 'count' items by cycling base_samples
    samples: List[Dict[str, Any]] = []
    for i in range(max(1, count)):
        src = base_samples[i % len(base_samples)]
        samples.append(
            {
                "id": uuid.uuid4().hex,
                "content": src["content"],
                "hashtags": src["hashtags"],
                "status": "approved",
                "created_at": now,
                "li_post_id": None,
                "error_message": None,
            }
        )

    existing.extend(samples)
    _save_session_list(request, "approved", existing)

    logger.info("Generated %d approved posts", len(samples))
    return {"ok": True, "approved_count": len(samples), "batch_id": uuid.uuid4().hex, "items": samples}

# ------------------------------------------------------------------------------
# Utility endpoints
# ------------------------------------------------------------------------------
@app.get("/api/config")
def api_config():
    return {
        "ok": True,
        "portal_base_url": FRONTEND_BASE_URL,
        "api_base": API_BASE_URL or "auto",
        "deployment_url": DEPLOYMENT_URL,
        "suggested_redirect_uri": SUGGESTED_REDIRECT,
        "cors_allow_origins": CORS_ORIGINS,
    }

@app.post("/api/logout")
def logout(request: Request):
    request.session.clear()
    logger.info("User logged out")
    return {"ok": True, "message": "Logged out successfully"}

# ------------------------------------------------------------------------------
# Error handlers
# ------------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error("HTTP Exception: %s - %s", exc.status_code, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "An internal error occurred. Please try again later."})
