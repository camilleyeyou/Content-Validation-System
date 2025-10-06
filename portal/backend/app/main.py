# portal/backend/app/main.py
from __future__ import annotations

import os
import uuid
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests
from fastapi import FastAPI, Request, Body, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

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

# Sessions (Secure, cross-site)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "dev-secret-change-me"),
    same_site="none",     # cross-site cookie for Vercel->Railway
    https_only=True,      # marks cookie Secure
    max_age=60 * 60 * 24 * 7,  # 7 days
)

FRONTEND_BASE_URL = (
    os.getenv("PORTAL_BASE_URL")
    or os.getenv("FRONTEND_BASE_URL")
    or "https://content-validation-system.vercel.app"
)
API_BASE_URL = os.getenv("API_BASE_URL") or ""  # purely informational

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
        raise HTTPException(status_code=401, detail="Not authenticated")
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
    return LinkedInSettingsOut(
        client_id=cfg.get("client_id") if cfg else None,
        redirect_uri=cfg.get("redirect_uri") if cfg else None,
        has_secret=bool(cfg and cfg.get("client_secret")),
        portal_base_url=FRONTEND_BASE_URL,
        api_base=API_BASE_URL or "auto",
    )

@app.post("/api/settings/linkedin")
def post_settings_linkedin(payload: LinkedInSettingsIn, request: Request):
    # Store into the session so each user can bring their own LinkedIn app.
    request.session["linkedin_settings"] = {
        "client_id": payload.client_id.strip(),
        "client_secret": payload.client_secret.strip(),
        "redirect_uri": payload.redirect_uri.strip(),
    }
    return {"ok": True, "message": "LinkedIn settings saved to session"}

# ------------------------------------------------------------------------------
# LinkedIn OAuth
# ------------------------------------------------------------------------------

@app.get("/auth/linkedin/login")
def linkedin_login(request: Request, include_org: bool = False, redirect: Optional[str] = None):
    cfg = get_linkedin_settings(request)
    if not cfg:
        return JSONResponse({"detail": "LinkedIn settings are missing"}, status_code=400)

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
    return RedirectResponse(url=auth_url, status_code=307)

@app.get("/auth/linkedin/callback")
def linkedin_callback(request: Request, code: str, state: Optional[str] = None):
    cfg = get_linkedin_settings(request)
    if not cfg:
        return JSONResponse({"detail": "LinkedIn settings are missing"}, status_code=400)

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": str(cfg["redirect_uri"]),  # avoid AnyHttpUrl problem
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
    }

    try:
        r = requests.post(token_url, data=data, timeout=20)
        r.raise_for_status()
        token = r.json()  # access_token, expires_in, (maybe) id_token
    except Exception as e:
        return JSONResponse({"detail": f"Token exchange failed: {e}"}, status_code=400)

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
    except Exception:
        pass

    # stash both
    request.session["li_token"] = token
    if profile:
        request.session["li_profile"] = profile

    # bounce back to where the user started
    dest = request.session.pop("post_login_redirect", None) or FRONTEND_BASE_URL or "/"
    sep = "&" if "?" in dest else "?"
    return RedirectResponse(url=f"{dest}{sep}app_session=1", status_code=307)

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

    return {"sub": sub, "name": name, "email": email, "org_preferred": request.session.get("org_preferred")}

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
            # front-end tolerates 400/401/403 here; don't crash.
            return JSONResponse({"error": "Cannot fetch organizations"}, status_code=resp.status_code)
        data = resp.json()
        orgs: List[Dict[str, str]] = []
        for el in data.get("elements", []):
            org = el.get("organization~") or {}
            oid = str(org.get("id") or "")
            urn = f"urn:li:organization:{oid}" if oid else ""
            if oid:
                orgs.append({"id": oid, "urn": urn})
        return {"orgs": orgs}
    except Exception:
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
    items = _session_list(request, "approved")
    idset = set(payload.ids)

    success = 0
    results: List[Dict[str, Any]] = []

    for it in items:
        if it.get("id") in idset:
            it["status"] = "published" if payload.publish_now else "draft"
            it["li_post_id"] = it.get("li_post_id") or f"mock-{uuid.uuid4().hex[:12]}"
            success += 1
            results.append({"id": it["id"], "status": it["status"], "li_post_id": it["li_post_id"]})

    _save_session_list(request, "approved", items)
    return {"successful": success, "results": results}

@app.post("/api/approved/clear")
def post_clear(request: Request):
    items = _session_list(request, "approved")
    deleted = len(items)
    _save_session_list(request, "approved", [])
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
    return {"approved_count": len(samples), "batch_id": uuid.uuid4().hex}

# ------------------------------------------------------------------------------
# Small utility
# ------------------------------------------------------------------------------

@app.get("/api/config")
def api_config():
    return {
        "portal_base_url": FRONTEND_BASE_URL,
        "api_base": API_BASE_URL or "auto",
        "cors_allow_origins": CORS_ORIGINS,
    }
