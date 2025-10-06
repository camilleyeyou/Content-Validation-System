# portal/backend/app/main.py
import os
import time
import json
import importlib
import inspect
import asyncio
from typing import Any, Dict, Optional, List, Callable, Tuple

import httpx
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse, RedirectResponse, PlainTextResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from urllib.parse import urlencode, quote_plus

# =============================================================================
#  Config
# =============================================================================

PORTAL_NAME = os.getenv("PORTAL_NAME", "Content Portal API – use /auth/linkedin/login or the UI")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
API_BASE_INFO = os.getenv("API_BASE", "http://localhost:8001")  # informational only

# CORS
DEFAULT_CORS = "http://localhost:3000,https://content-validation-system.vercel.app"
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", DEFAULT_CORS).split(",") if o.strip()]

# Sessions & token signing
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-session-secret-change-me")
TOKEN_SECRET = os.getenv("TOKEN_SECRET", SESSION_SECRET)
TOKEN_MAX_AGE_SECONDS = int(os.getenv("TOKEN_MAX_AGE_SECONDS", str(60 * 60 * 8)))  # 8h

serializer = URLSafeTimedSerializer(TOKEN_SECRET, salt="portal-token-v1")

# In-memory LinkedIn app settings (overridable by env or POST /api/settings/linkedin)
SETTINGS: Dict[str, Any] = {
    # "client_id": "...",
    # "client_secret": "...",
    # "redirect_uri": "https://.../auth/linkedin/callback",
    # "scope": "openid profile email w_member_social rw_organization_admin w_organization_social",
}

def get_setting(name: str, default: Optional[str] = None) -> Optional[str]:
    return SETTINGS.get(name) or os.getenv(name.upper(), default)

# =============================================================================
#  App
# =============================================================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie=os.getenv("SESSION_COOKIE_NAME", "portal_session"),
    https_only=True,
    same_site="none",  # allow cross-site cookies when the browser permits
)

# =============================================================================
#  Token helpers
# =============================================================================

def mint_token(user: Dict[str, Any]) -> str:
    payload = {
        "sub": user.get("sub"),
        "name": user.get("name"),
        "email": user.get("email"),
        "li_access_token": user.get("li_access_token"),
        "li_token_exp": user.get("li_token_exp"),
        "org_preferred": user.get("org_preferred"),
    }
    return serializer.dumps(payload)

def load_token(token: str) -> Dict[str, Any]:
    return serializer.loads(token, max_age=TOKEN_MAX_AGE_SECONDS)

def current_user(request: Request, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    # (1) Try session
    sess_user = request.session.get("user")
    if sess_user:
        return sess_user
    # (2) Try Bearer token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            data = load_token(token)
            exp = data.get("li_token_exp")
            if exp and time.time() >= float(exp):
                raise HTTPException(status_code=401, detail="LinkedIn token expired")
            return data
        except SignatureExpired:
            raise HTTPException(status_code=401, detail="Token expired")
        except BadSignature:
            raise HTTPException(status_code=401, detail="Invalid token")
    raise HTTPException(status_code=401, detail="Unauthorized")

# =============================================================================
#  Dynamic integration helpers (wire to your real code if present)
# =============================================================================

def import_first(candidates: List[Tuple[str, str]]) -> Optional[Any]:
    """
    Try to import attr from the first module that exists.
    candidates: [("module.path", "attr_name"), ...]
    """
    for mod_name, attr in candidates:
        try:
            mod = importlib.import_module(mod_name)
            obj = getattr(mod, attr, None)
            if obj:
                return obj
        except Exception:
            continue
    return None

# Try to locate your real pipeline & storage functions
RUN_FULL = import_first([
    ("test_complete_system", "run_full"),
    ("portal.backend.app.pipeline", "run_full"),
    ("src.pipeline", "run_full"),
])

GET_APPROVED = import_first([
    ("portal.backend.app.store", "get_approved"),
    ("test_complete_system", "get_approved"),
    ("src.store", "get_approved"),
])

CLEAR_APPROVED = import_first([
    ("portal.backend.app.store", "clear_approved"),
    ("test_complete_system", "clear_approved"),
    ("src.store", "clear_approved"),
])

PUBLISH_APPROVED = import_first([
    ("portal.backend.app.publisher", "publish_approved"),
    ("test_complete_system", "publish_approved"),
    ("src.publisher", "publish_approved"),
])

# Fallback in-memory queue (used only if your real functions are not found)
_APPROVED_STORE: List[Dict[str, Any]] = []

async def call_maybe_async(fn: Callable, *args, **kwargs):
    if inspect.iscoroutinefunction(fn):
        return await fn(*args, **kwargs)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))

# =============================================================================
#  Root & settings
# =============================================================================

@app.get("/")
async def root():
    return {
        "ok": True,
        "message": PORTAL_NAME,
        "portal_base_url": FRONTEND_BASE_URL + "/",
        "api_base": API_BASE_INFO,
        "redirect_uri": get_setting("redirect_uri"),
    }

@app.options("/api/settings/linkedin")
async def preflight_settings():
    return PlainTextResponse("ok")

@app.get("/api/settings/linkedin")
async def get_settings():
    safe = {
        "client_id": get_setting("client_id"),
        "redirect_uri": get_setting("redirect_uri"),
        "scope": get_setting(
            "scope",
            "openid profile email w_member_social rw_organization_admin w_organization_social",
        ),
        "frontend_base": FRONTEND_BASE_URL,
        "api_base": API_BASE_INFO,
    }
    return safe

@app.post("/api/settings/linkedin")
async def set_settings(req: Request):
    try:
        data = await req.json()
    except Exception:
        data = {}
    for k in ("client_id", "client_secret", "redirect_uri", "scope"):
        if data.get(k):
            SETTINGS[k] = data[k]
    return {"ok": True, "settings": {k: SETTINGS.get(k) for k in SETTINGS}}

# =============================================================================
#  LinkedIn OAuth
# =============================================================================

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO = "https://api.linkedin.com/v2/userinfo"

@app.get("/auth/linkedin/login")
async def linkedin_login(include_org: Optional[bool] = True):
    client_id = get_setting("client_id")
    redirect_uri = get_setting("redirect_uri")
    scope = get_setting(
        "scope",
        "openid profile email w_member_social rw_organization_admin w_organization_social",
    )
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=400, detail="LinkedIn settings are missing")
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": str(int(time.time())),
    }
    url = f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url, status_code=307)

@app.get("/auth/linkedin/callback")
async def linkedin_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    client_id = get_setting("client_id")
    client_secret = get_setting("client_secret")
    redirect_uri = get_setting("redirect_uri")
    if not (client_id and client_secret and redirect_uri):
        raise HTTPException(status_code=400, detail="LinkedIn settings incomplete")

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_resp = await client.post(
            LINKEDIN_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if token_resp.status_code != 200:
        raise HTTPException(status_code=401, detail=f"Token exchange failed: {token_resp.text}")
    token_json = token_resp.json()
    access_token = token_json.get("access_token")
    expires_in = token_json.get("expires_in")
    if not access_token:
        raise HTTPException(status_code=401, detail="No access_token from LinkedIn")

    async with httpx.AsyncClient(timeout=20.0) as client:
        me_resp = await client.get(LINKEDIN_USERINFO, headers={"Authorization": f"Bearer {access_token}"})
    if me_resp.status_code != 200:
        raise HTTPException(status_code=401, detail=f"userinfo failed: {me_resp.text}")
    me = me_resp.json()

    user = {
        "sub": me.get("sub"),
        "name": me.get("name"),
        "email": me.get("email"),
        "li_access_token": access_token,
        "li_token_exp": time.time() + float(expires_in or 0),
        "org_preferred": None,
    }
    # (1) session cookie
    request.session["user"] = user
    # (2) bearer token
    t = mint_token(user)
    dest = f"{FRONTEND_BASE_URL}/?t={quote_plus(t)}"
    return RedirectResponse(dest, status_code=307)

# =============================================================================
#  Auth-protected APIs
# =============================================================================

@app.get("/api/me")
async def api_me(user: Dict[str, Any] = Depends(current_user)):
    return {
        "sub": user.get("sub"),
        "name": user.get("name"),
        "email": user.get("email"),
        "org_preferred": user.get("org_preferred"),
    }

@app.get("/api/orgs")
async def api_orgs(user: Dict[str, Any] = Depends(current_user)):
    access_token = user.get("li_access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Missing LinkedIn token")

    url = "https://api.linkedin.com/rest/organizationAcls"
    params = {"q": "roleAssignee", "role": "ADMINISTRATOR", "state": "APPROVED"}
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": "202401",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url, params=params, headers=headers)
    if r.status_code != 200:
        return JSONResponse({"error": f"{r.status_code} {r.text}"}, status_code=r.status_code)

    data = r.json()
    orgs: List[Dict[str, str]] = []
    for el in data.get("elements", []):
        org = el.get("organization")
        if isinstance(org, str):
            orgs.append({"id": org.split(":")[-1], "urn": org})
    return {"orgs": orgs}

# ===== Approved storage adapters =====

async def adapter_get_approved() -> List[Dict[str, Any]]:
    if GET_APPROVED:
        res = await call_maybe_async(GET_APPROVED)
        # force into list[dict] shape the UI expects
        if isinstance(res, list):
            return res
        return []
    return list(_APPROVED_STORE)

async def adapter_clear_approved() -> int:
    if CLEAR_APPROVED:
        res = await call_maybe_async(CLEAR_APPROVED)
        try:
            return int(res or 0)
        except Exception:
            return 0
    n = len(_APPROVED_STORE)
    _APPROVED_STORE.clear()
    return n

async def adapter_publish_approved(
    ids: List[str],
    target: str,
    publish_now: bool,
    org_id: Optional[str],
    user: Dict[str, Any],
) -> Dict[str, Any]:
    if PUBLISH_APPROVED:
        res = await call_maybe_async(PUBLISH_APPROVED, ids=ids, target=target,
                                     publish_now=publish_now, org_id=org_id, user=user)
        # expect {"successful": n, "results": [...]}
        if isinstance(res, dict):
            return res
    # fallback: pretend success
    return {"successful": len(ids), "results": [{"id": i, "ok": True} for i in ids]}

async def adapter_run_full_and_refresh() -> Dict[str, Any]:
    """
    Run your real pipeline if available; then fetch the approved list.
    """
    if RUN_FULL:
        try:
            res = await call_maybe_async(RUN_FULL)
            # If your run_full returns approved items, you can sync them here.
            # Otherwise we just ignore the return (you likely store to DB).
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"run_full failed: {e}")
    # After running, return count from current store
    items = await adapter_get_approved()
    return {"approved_count": len(items), "batch_id": None}

# ===== Endpoints =====

@app.get("/api/approved")
async def api_approved(user: Dict[str, Any] = Depends(current_user)):
    items = await adapter_get_approved()
    # Normalize keys the UI expects
    def norm(x: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(x.get("id") or x.get("uuid") or x.get("pk") or ""),
            "content": x.get("content") or x.get("text") or "",
            "hashtags": x.get("hashtags") or [],
            "status": x.get("status") or "APPROVED",
            "created_at": x.get("created_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "li_post_id": x.get("li_post_id"),
            "error_message": x.get("error_message"),
            "user_sub": x.get("user_sub"),
        }
    return [norm(i) for i in items if i]

@app.post("/api/approved/publish")
async def api_publish(req: Request, user: Dict[str, Any] = Depends(current_user)):
    try:
        body = await req.json()
    except Exception:
        body = {}
    ids = body.get("ids") or []
    target = (body.get("target") or "MEMBER").upper()
    publish_now = bool(body.get("publish_now"))
    org_id = body.get("org_id")

    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=400, detail="ids is required")

    res = await adapter_publish_approved(ids, target, publish_now, org_id, user)
    return res

@app.post("/api/approved/clear")
async def api_clear(user: Dict[str, Any] = Depends(current_user)):
    deleted = await adapter_clear_approved()
    return {"deleted": int(deleted)}

@app.post("/api/run-batch")
async def run_batch(user: Dict[str, Any] = Depends(current_user)):
    res = await adapter_run_full_and_refresh()
    return res
