import os
import time
import secrets
import urllib.parse
from typing import Optional, Dict, Tuple

import requests
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, AnyHttpUrl

# =========================
# App & CORS
# =========================

app = FastAPI(title="Content Portal API")

def _parse_origins() -> list[str]:
    """
    FRONTEND_ORIGINS may be a comma-separated list, e.g.:
    https://content-validation-system.vercel.app,https://www.myportal.com,http://localhost:3000
    """
    raw = os.getenv("FRONTEND_ORIGINS") or os.getenv("FRONTEND_ORIGIN") or ""
    if not raw.strip():
        # Safe defaults for local + your Vercel preview/prod + any 127.0.0.1
        defaults = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://content-validation-system.vercel.app",
        ]
        return defaults
    return [o.strip() for o in raw.split(",") if o.strip()]

ALLOWED_ORIGINS = _parse_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

# =========================
# Home (diagnostic)
# =========================

@app.get("/")
def root():
    portal_base = os.getenv("PORTAL_BASE_URL", "https://content-validation-system.vercel.app/")
    api_base = os.getenv("API_BASE", "http://localhost:8001")
    redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", "")
    return {
        "ok": True,
        "message": "Content Portal API – use /auth/linkedin/login or the UI",
        "portal_base_url": portal_base,
        "api_base": api_base,
        "redirect_uri": redirect_uri,
        "allowed_origins": ALLOWED_ORIGINS,
    }

# =========================
# Stateless settings store (sid-based)
# =========================

class LoginSettingsIn(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: AnyHttpUrl
    scope: Optional[str] = None           # space-separated
    include_org_default: Optional[bool] = True

class LoginSettingsStore:
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self._store: Dict[str, Tuple[float, dict]] = {}

    def put(self, data: dict) -> str:
        sid = secrets.token_urlsafe(16)
        self._store[sid] = (time.time(), data)
        return sid

    def get(self, sid: Optional[str]) -> Optional[dict]:
        if not sid:
            return None
        item = self._store.get(sid)
        if not item:
            return None
        ts, data = item
        if time.time() - ts > self.ttl:
            self._store.pop(sid, None)
            return None
        return data

app.state.login_settings = LoginSettingsStore(ttl_seconds=3600)

def _env_linkedin_cfg() -> Optional[dict]:
    cid = os.getenv("LINKEDIN_CLIENT_ID")
    csec = os.getenv("LINKEDIN_CLIENT_SECRET")
    ruri = os.getenv("LINKEDIN_REDIRECT_URI")
    scope = os.getenv("LINKEDIN_SCOPE")  # optional; space-separated
    if cid and csec and ruri:
        return {
            "client_id": cid,
            "client_secret": csec,
            "redirect_uri": ruri,
            "scope": scope,
            "include_org_default": True,
        }
    return None

# =========================
# Tiny portal token store (Bearer auth for /api/*)
# =========================

class TokenStore:
    def __init__(self, ttl_seconds: int = 3600 * 24):
        self.ttl = ttl_seconds
        self._store: Dict[str, Tuple[float, dict]] = {}

    def mint(self, payload: dict) -> str:
        tok = secrets.token_urlsafe(24)
        self._store[tok] = (time.time(), payload)
        return tok

    def get(self, token: Optional[str]) -> Optional[dict]:
        if not token:
            return None
        item = self._store.get(token)
        if not item:
            return None
        ts, data = item
        if time.time() - ts > self.ttl:
            self._store.pop(token, None)
            return None
        return data

app.state.tokens = TokenStore(ttl_seconds=3600 * 24)

def _auth_from_header(authorization: Optional[str]) -> Optional[dict]:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    return app.state.tokens.get(token)

# =========================
# Settings endpoints
# =========================

@app.options("/api/settings/linkedin")
def _options_settings():
    return JSONResponse({"ok": True})

@app.get("/api/settings/linkedin")
def get_linkedin_settings(request: Request, sid: Optional[str] = None):
    if sid:
        data = app.state.login_settings.get(sid)
        if data:
            return {
                "sid": sid,
                "client_id": data["client_id"],
                "redirect_uri": data["redirect_uri"],
                "scope": data.get("scope") or "",
                "include_org_default": data.get("include_org_default", True),
            }
    env_cfg = _env_linkedin_cfg()
    return {
        "env_config_present": bool(env_cfg),
        "client_id": (env_cfg or {}).get("client_id") and True or False,
        "redirect_uri": (env_cfg or {}).get("redirect_uri"),
    }

@app.post("/api/settings/linkedin")
def save_linkedin_settings(payload: LoginSettingsIn):
    sid = app.state.login_settings.put(payload.model_dump())
    return {"ok": True, "sid": sid}

# =========================
# LinkedIn OAuth
# =========================

DEFAULT_MEMBER_SCOPES = "openid profile email w_member_social"
ORG_SCOPES = "rw_organization_admin w_organization_social"

def _build_authorize_url(client_id: str, redirect_uri: str, scope_str: str, state: str) -> str:
    base = "https://www.linkedin.com/oauth/v2/authorization"
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope_str.strip(),
        "state": state,
    }
    return f"{base}?{urllib.parse.urlencode(params)}"

def _extract_sid_from_state(state: str) -> Optional[str]:
    # state either "<random>" or "sid:<sid>:<random>"
    if state and state.startswith("sid:"):
        try:
            _, sid, _ = state.split(":", 2)
            return sid or None
        except Exception:
            return None
    return None

@app.get("/auth/linkedin/login")
def linkedin_login(include_org: bool = True, sid: Optional[str] = None):
    cfg = app.state.login_settings.get(sid) if sid else None
    if not cfg:
        cfg = _env_linkedin_cfg()
    if not cfg:
        raise HTTPException(status_code=400, detail="LinkedIn settings are missing")

    scope = cfg.get("scope") or DEFAULT_MEMBER_SCOPES
    if include_org:
        # ensure org scopes are present
        for s in ORG_SCOPES.split():
            if s not in scope.split():
                scope = f"{scope} {s}"

    rand = secrets.token_urlsafe(8)
    state = f"sid:{sid}:{rand}" if sid else rand

    url = _build_authorize_url(cfg["client_id"], cfg["redirect_uri"], scope, state)
    return RedirectResponse(url, status_code=307)

@app.get("/auth/linkedin/callback")
def linkedin_callback(code: str, state: str):
    sid = _extract_sid_from_state(state)
    cfg = app.state.login_settings.get(sid) if sid else _env_linkedin_cfg()
    if not cfg:
        raise HTTPException(status_code=400, detail="LinkedIn settings are missing")

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": cfg["redirect_uri"],
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
    }
    # exchange code for token
    r = requests.post(token_url, data=data, timeout=20)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {r.text}")
    tok = r.json()
    access_token = tok.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access_token in response")

    # Fetch user basic profile (v2 me or OpenID depends on scopes; try v2/me)
    hdrs = {"Authorization": f"Bearer {access_token}"}
    me_resp = requests.get("https://api.linkedin.com/v2/userinfo", headers=hdrs, timeout=20)
    if me_resp.status_code != 200:
        # fallback older API
        me_resp = requests.get("https://api.linkedin.com/v2/me", headers=hdrs, timeout=20)
    me = me_resp.json() if me_resp.ok else {}

    # mint portal token
    payload = {
        "li_access_token": access_token,
        "li_profile": me,
        "org_scopes": any(s in (cfg.get("scope") or "") for s in ORG_SCOPES.split()),
    }
    portal_token = app.state.tokens.mint(payload)

    # redirect back to portal with ?t=
    portal_base = os.getenv("PORTAL_BASE_URL", "https://content-validation-system.vercel.app/")
    if not portal_base.endswith("/"):
        portal_base += "/"
    return RedirectResponse(f"{portal_base}?t={portal_token}", status_code=307)

# =========================
# Minimal helpers for UI
# =========================

@app.get("/api/me")
def api_me(authorization: Optional[str] = Header(None)):
    user = _auth_from_header(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    prof = user.get("li_profile") or {}
    sub = prof.get("sub") or prof.get("id") or "me"
    name = prof.get("name") or prof.get("localizedFirstName") or "LinkedIn User"
    email = prof.get("email") or None
    return {"sub": sub, "name": name, "email": email, "org_preferred": None}

@app.get("/api/orgs")
def api_orgs(authorization: Optional[str] = Header(None)):
    user = _auth_from_header(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not user.get("org_scopes"):
        # You can still try—LinkedIn will 403; surface as 403 to the UI
        raise HTTPException(status_code=403, detail="Missing organization scopes")

    tok = user["li_access_token"]
    hdrs = {"Authorization": f"Bearer {tok}"}
    # List organizations the user manages — adjust to your exact needs
    resp = requests.get(
        "https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee&state=APPROVED&count=50",
        headers=hdrs, timeout=20
    )
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    data = resp.json()
    orgs = []
    for el in data.get("elements", []):
        urn = el.get("organizationalTarget", "")
        if urn:
            orgs.append({"id": urn.split(":")[-1], "urn": urn})
    return {"orgs": orgs}
